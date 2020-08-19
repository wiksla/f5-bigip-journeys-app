import hashlib
import os
import shelve
import shutil
from typing import Optional

import click
from git import Repo
from gitdb.exc import BadName

from journeys.config import Config
from journeys.modifier.conflict.handler import ConflictHandler
from journeys.utils.ucs_ops import tar_file
from journeys.utils.ucs_ops import untar_file
from journeys.utils.ucs_reader import UcsReader


def md5(fname):
    hash_md5 = hashlib.md5()
    with open(fname, "rb") as f:
        for chunk in iter(lambda: f.read(4096), b""):
            hash_md5.update(chunk)
    return hash_md5.hexdigest()


class MigrationController:
    SHELF_FILE_NAME = ".shelf"
    REPO_FOLDER_NAME = "wip"

    def __init__(
        self,
        input_ucs: Optional[str] = None,
        output_ucs: Optional[str] = None,
        clear: bool = False,
    ):
        working_directory = os.environ.get("MIGRATE_DIR", ".")

        self.input_ucs = input_ucs
        self.working_directory = working_directory
        if not os.path.exists(self.working_directory):
            os.mkdir(self.working_directory)

        self.repo_path = os.path.join(self.working_directory, self.REPO_FOLDER_NAME)
        self.shelf_path = os.path.join(self.repo_path, self.SHELF_FILE_NAME)

        if clear:
            shutil.rmtree(self.repo_path, ignore_errors=True)

        if not os.path.exists(self.repo_path):
            os.mkdir(self.repo_path)

        self.repo = Repo.init(self.repo_path)
        self.config_path = os.path.join(self.repo_path, "config")
        self.shelf = shelve.open(self.shelf_path)

        self.output_ucs = (
            output_ucs
            or self.shelf.get("ucs", "").replace(".ucs", ".modified.ucs")
            or "journeys.ucs"
        )

        self.ucs_reader = None
        self.config = None
        self.conflict_handler = None

    def prompt(self):

        current_conflict = self.shelf.get("current_conflict", None)
        conflicts = self.shelf.get("conflicts", None)

        if current_conflict:
            prompt = f" ({current_conflict})"
        elif conflicts:
            prompt = f" ({len(conflicts)} conflicts left)"
        else:
            prompt = ""

        return f"\\e[1;32mjourney{prompt}: \\e[0m"

    def process(self):
        if not self._check_master():
            click.echo("Please checkout to master branch.")
            return

        if self.input_ucs:
            file_hash = md5(self.input_ucs)

            stored_file_hash = self.shelf.get("file_hash", None)
            if stored_file_hash and stored_file_hash != file_hash:
                click.echo("Different ucs file received as an input.")
                click.echo(
                    f"In order to start processing new ucs file run journey.py migrate {self.input_ucs} --clear"
                )
                return

            self.shelf["file_hash"] = file_hash

        self._ensure_repo_initialized()

        if self.config is None:
            self._read_config()
        conflicts = self.conflict_handler.detect_conflicts()
        self.shelf["conflicts"] = list(conflicts.keys())

        current_conflict = self.shelf.get("current_conflict", None)
        if current_conflict:
            if current_conflict not in conflicts:
                if self.repo.is_dirty():
                    self.repo.git.add(u=True)
                    self.repo.index.commit(message=current_conflict)
                self.shelf["current_conflict"] = ""
            else:
                click.echo(
                    f"ERROR: Current conflict {current_conflict} is not yet resolved.\n"
                )
                self._print_conflict_resolution_help(conflicts[current_conflict])
                return

        for head in self.repo.heads:
            if head not in [self.repo.heads.master, self.repo.heads.initial]:
                head.delete(self.repo, head, force=True)

        if conflicts:
            self._print_conflicts_info(conflicts)
            return

        if not self.repo.heads.initial.commit == self.repo.heads.master.commit:
            click.echo("All conflicts have been resolved.")

            output_ucs = self._create_output_ucs()
            click.echo(f"Output ucs has been stored as {output_ucs}.")
        else:
            click.echo("No known issues found in the given ucs.")

    def resolve(self, conflict_id):

        current_conflict = self.shelf.get("current_conflict", None)
        if current_conflict and current_conflict != conflict_id:
            click.echo(
                f"Conflict {current_conflict} resolution already in progress."
                "Finish it by calling 'journey.py migrate' first before starting a new one."
            )
            return

        if self.config is None:
            self._read_config()
        conflicts = self.conflict_handler.detect_conflicts()

        if conflict_id not in conflicts:
            click.echo("Invalid conflict ID - given conflict not found in the config.")
            return

        conflict = conflicts[conflict_id]
        self.shelf["current_conflict"] = conflict_id

        for mitigation in conflict.mitigations:
            if mitigation == "comment_only":
                # leave "comment" solution for the end - we want to keep it on master,
                # and we want to branch off from non-commented files
                continue

            branch_name = f"{conflict_id}_{mitigation}"
            if branch_name not in self.repo.heads:
                self.repo.create_head(f"{conflict_id}_{mitigation}").checkout()
                self.conflict_handler.render(
                    dirname=self.config_path, conflict=conflict, mitigation=mitigation,
                )
                self.repo.git.add(u=True)
                self.repo.index.commit(mitigation)

        self.repo.heads.master.checkout()
        self.conflict_handler.render(
            dirname=self.config_path, conflict=conflict, mitigation="comment_only",
        )
        self._print_conflict_resolution_help(conflict)

    def _read_config(self):
        self.ucs_reader = UcsReader(extracted_ucs_dir=self.repo_path)
        self.config: Config = self.ucs_reader.get_config()
        self.conflict_handler = ConflictHandler(self.config)

    def _check_master(self):
        return self.repo.active_branch.name == "master"

    def _ensure_repo_initialized(self):

        try:
            self.repo.commit("initial")
        except BadName:
            if not self.input_ucs:
                raise RuntimeError(
                    "No ucs file has been given and there is no session to resume."
                )
            _, files_metadata = untar_file(self.input_ucs, output_dir=self.repo_path)
            self.shelf["files_metadata"] = files_metadata
            with open(
                file=os.path.join(self.repo_path, ".gitignore"), mode="w"
            ) as gitignore:
                gitignore.write(".shelf.db")
            self.shelf["ucs"] = self.input_ucs
            self.repo.git.add("*")
            self.repo.index.commit("initial")

            # rebuilding the config changes the formatting slightly -
            # do it here so that later diffs are clean
            ucs_reader = UcsReader(extracted_ucs_dir=os.path.join(self.repo_path))
            config: Config = ucs_reader.get_config()
            config.build(dirname=self.config_path)
            self.repo.git.add(u=True)
            self.repo.index.commit("reformat")
            self.repo.create_head("initial")

    def _create_output_ucs(self):
        try:
            os.remove(self.output_ucs)
        except FileNotFoundError:
            pass

        output_path = os.path.join(
            self.working_directory, os.path.basename(self.output_ucs)
        )
        tar_file(
            archive_file=output_path,
            input_dir=os.path.join(self.repo_path),
            files_metadata=self.shelf["files_metadata"],
        )
        return output_path

    def _print_conflicts_info(self, conflicts):
        click.echo("There are following conflicts waiting to be resolved:")
        for _id, conflict in conflicts.items():
            click.echo("")
            click.echo(f"{conflict.id}:")
            for line in conflict.summary:
                click.echo(f"\t{line}")
        click.echo("")
        click.echo("Please run 'journey.py resolve <Conflict>' to apply sample fixes.")
        click.echo(f"Example 'journey.py resolve {next(iter(conflicts.keys()))}'")

    def _print_conflict_resolution_help(self, conflict):
        click.echo(f"Workdir: {self.working_directory}")
        click.echo(f"Config path: {self.config_path}\n")
        click.echo(f"Resolving conflict {conflict.id}\n")
        click.echo(
            f"Resolve the issues on objects commented with '{conflict.id}' in the following files:"
        )
        for filename in conflict.files_to_render:
            click.echo(f"\t{filename}")

        click.echo("")
        click.echo(
            f"Proposed fixes are present in branches (in git repository: {self.repo_path}):"
        )
        for mitigation in conflict.mitigations:
            if mitigation == "comment_only":
                continue

            click.echo(f"\t{conflict.id}_{mitigation}")
        click.echo("")
        click.echo(
            f"To view the issues found, enter the {self.repo_path} directory and check the diff of the current branch "
            f"(e.g. 'git diff') "
        )
        click.echo(
            "To view the proposed changes, you can use any git diff tool (e.g. 'git diff master..<branch_name>')"
        )
        click.echo(
            "To apply proposed changes right away, you can merge one of the branches "
            "(e.g. 'git checkout . ; git merge <branch_name>')"
        )
        click.echo("  Alternatively, you can edit the files manually.")
        click.echo("")
        click.echo(
            "You do not have to commit your changes - just apply them in the specified files."
        )
        click.echo("Run 'journey.py migrate' once you're finished.")
