import logging
import os
import shelve
import shutil
from tarfile import ReadError

from git import Repo
from gitdb.exc import BadName

from journeys.config import Config
from journeys.errors import AlreadyInitializedError
from journeys.errors import ArchiveDecryptError
from journeys.errors import ArchiveOpenError
from journeys.errors import ConflictNotResolvedError
from journeys.errors import DifferentConflictError
from journeys.errors import NotAllConflictResolvedError
from journeys.errors import NotInitializedError
from journeys.errors import NotMasterBranchError
from journeys.errors import OutputAlreadyExistsError
from journeys.modifier.conflict.conflict import Conflict
from journeys.modifier.conflict.handler import ConflictHandler
from journeys.utils.ucs_ops import tar_file
from journeys.utils.ucs_ops import untar_file
from journeys.utils.ucs_reader import UcsReader

log = logging.getLogger(__name__)

WORKDIR = os.environ.get("MIGRATE_DIR", ".")


def setup_logging(level=logging.DEBUG):
    log_file = os.path.join(WORKDIR, "journeys.log")

    format_string = "%(asctime)s %(name)s [%(levelname)s] %(message)s"
    formatter = logging.Formatter(format_string)

    handler = logging.FileHandler(log_file)
    handler.setLevel(level)
    handler.setFormatter(formatter)

    log = logging.getLogger()
    log.setLevel(level)
    log.addHandler(handler)


class MigrationController:
    SHELF_FILE_NAME = ".shelf"
    REPO_FOLDER_NAME = "wip"

    def __init__(self, clear=False, allow_empty=False):

        self.repo_path = os.path.join(WORKDIR, self.REPO_FOLDER_NAME)
        if clear:
            log.info(f"Clear enabled - removing {self.repo_path}.")
            shutil.rmtree(self.repo_path, ignore_errors=True)
        if not os.path.exists(self.repo_path):
            os.mkdir(self.repo_path)

        self.config_path = os.path.join(self.repo_path, "config")

        self.repo = Repo.init(self.repo_path)
        self.shelf = shelve.open(os.path.join(self.repo_path, self.SHELF_FILE_NAME))

        self.ucs_reader = None
        self.config = None
        self.conflict_handler = None

        self._ensure_is_master()

        if not allow_empty:
            self._ensure_is_initialized()

    def initialize(self, input_ucs, ucs_passphrase):

        if self._is_repo_initialized():
            raise AlreadyInitializedError(input=input_ucs)

        log.info("Initializing the git repository.")

        try:
            log.info(f"Unpacking the provided file {input_ucs} into {self.repo_path}.")
            _, files_metadata = untar_file(
                input_ucs, output_dir=self.repo_path, archive_passphrase=ucs_passphrase,
            )
        except ReadError:
            raise ArchiveOpenError()
        except RuntimeError:
            raise ArchiveDecryptError()

        self.shelf["input_ucs_name"] = os.path.basename(input_ucs)
        self.shelf["files_metadata"] = files_metadata
        self._add_shelf_file_to_gitignore()
        log.info("Preparing the initial commit.")
        self.repo.git.add("*")
        self.repo.index.commit("initial")

        # rebuilding the config changes the formatting slightly -
        # do it here so that later diffs are clean
        self._read_config()
        log.info("Preparing the reformat commit.")
        self.config.build(dirname=self.config_path)
        self.repo.git.add(u=True)
        self.repo.index.commit("reformat")
        self.repo.create_head("initial")

    @property
    def current_conflict(self):
        return self.shelf.get("current_conflict", None)

    def prompt(self):
        current_conflict = self.current_conflict
        conflicts = self.shelf.get("conflicts", None)

        if current_conflict:
            prompt = f"{current_conflict}"
        elif conflicts:
            prompt = f"{len(conflicts)} conflicts left"
        else:
            prompt = "No more conflicts"

        return prompt

    def process(self) -> dict:
        log.info("Initiating conflict search.")
        if self.config is None:
            self._read_config()
        conflicts = self.conflict_handler.get_conflicts()
        log.info(f"Conflicts found: {', '.join(conflicts.keys())}")
        self.shelf["conflicts"] = list(conflicts.keys())

        current_conflict = self.current_conflict
        if current_conflict:
            log.info(f"Conflict {current_conflict} is currently being resolved.")
            if current_conflict not in conflicts:
                log.info(f"Conflict {current_conflict} appears resolved. Continuing.")
                if self.repo.is_dirty():
                    uncommited = [diff.a_path for diff in self.repo.index.diff(None)]
                    log.info(
                        f"Uncommited changes found: {uncommited}. Creating a new commit."
                    )
                    self.repo.git.add(u=True)
                    self.repo.index.commit(message=current_conflict)
                self.shelf["current_conflict"] = ""
            else:
                raise ConflictNotResolvedError(
                    conflict_id=current_conflict,
                    conflict_info=conflicts[current_conflict],
                    working_directory=WORKDIR,
                    config_path=self.config_path,
                    mitigation_branches=self.get_mitigation_branches(),
                )

        self.remove_mitigations_branches()

        return conflicts

    def history(self):
        commits = list(self.repo.iter_commits(rev="initial...master"))
        commits.reverse()
        return commits

    def resolve(self, conflict_id: str):

        current_conflict = self.current_conflict
        if current_conflict and current_conflict != conflict_id:
            raise DifferentConflictError(conflict_id=current_conflict)

        if self.config is None:
            self._read_config()

        log.info(f"Initiating resolution for conflict {conflict_id}.")
        conflict_info = self.conflict_handler.get_conflict(conflict_id=conflict_id)
        self.shelf["current_conflict"] = conflict_id

        for mitigation in conflict_info.mitigations["mitigations"]:

            branch_name = f"{conflict_id}_{mitigation}"

            if self._mitigation_is_recommended(
                conflict_info=conflict_info, mitigation=mitigation
            ):
                branch_name = f"F5_Recommended_{conflict_id}_{mitigation}"

            log.info(f'Creating resolution branch "{branch_name}".')

            if branch_name not in self.repo.heads:
                self.repo.heads.master.checkout()
                self._create_mitigation_branch(
                    conflict_info=conflict_info,
                    branch_name=branch_name,
                    mitigation_func=conflict_info.mitigations["mitigations"][
                        mitigation
                    ],
                )

        self.repo.heads.master.checkout()
        log.info('Creating resolution branch "comment_only".')
        self.conflict_handler.render(
            dirname=self.config_path,
            conflict=conflict_info,
            mitigation_func=conflict_info.mitigations["comment_only"],
        )
        return (
            conflict_info,
            WORKDIR,
            self.config_path,
            self.get_mitigation_branches(),
        )

    def resolve_recommended(self):
        while True:
            conflicts = self.process()
            if not conflicts:
                log.info("All conflicts are resolved automatically successfully.")
                break

            _, conflict_info = conflicts.popitem()

            self.shelf["current_conflict"] = conflict_info.id
            mitigation_name = conflict_info.mitigations["recommended"].__name__
            branch_name = f"F5_Recommended_{conflict_info.id}_{mitigation_name}"
            log.info(f'Creating resolution branch "{branch_name}".')

            self.repo.heads.master.checkout()
            self._create_mitigation_branch(
                conflict_info=conflict_info,
                branch_name=branch_name,
                mitigation_func=conflict_info.mitigations["recommended"],
            )

            self.repo.heads.master.checkout()
            self.repo.git.checkout(".")
            self.repo.git.merge(branch_name)

            self._read_config()

    def generate(self, output, force, ucs_passphrase, overwrite):

        if self.config is None:
            self._read_config()

        if not force:
            if self.conflict_handler.get_conflicts():
                raise NotAllConflictResolvedError()

        output = output or self.shelf["input_ucs_name"].replace(".ucs", ".modified.ucs")

        output_ucs = self._create_output_ucs(
            output=output, ucs_passphrase=ucs_passphrase, overwrite=overwrite
        )
        return output_ucs

    def _ensure_is_master(self):
        if self.repo.active_branch.name != "master":
            raise NotMasterBranchError()

    def _ensure_is_initialized(self):
        if not self._is_repo_initialized():
            raise NotInitializedError()

    def _read_config(self):
        log.info(f"Reading and parsing the configuration from {self.repo_path}.")
        self.ucs_reader = UcsReader(extracted_ucs_dir=self.repo_path)
        self.config: Config = self.ucs_reader.get_config()
        self.conflict_handler = ConflictHandler(config=self.config)

    def _is_repo_initialized(self):
        try:
            self.repo.commit("initial")
        except BadName:
            return False

        return True

    def _create_output_ucs(self, output, ucs_passphrase, overwrite):

        output_path = os.path.join(WORKDIR, os.path.basename(output))

        if overwrite:
            try:
                os.remove(output_path)
                log.info(f"Old version of {output_path} found and removed.")
            except FileNotFoundError:
                pass

        if os.path.exists(output_path):
            raise OutputAlreadyExistsError(output=output_path)

        log.info(f"Creating output ucs {output}.")

        tar_file(
            archive_file=output_path,
            input_dir=os.path.join(self.repo_path),
            files_metadata=self.shelf["files_metadata"],
            archive_passphrase=ucs_passphrase,
        )
        return output_path

    def _add_shelf_file_to_gitignore(self):
        git_ignore_file = os.path.join(self.repo_path, ".gitignore")
        with open(file=git_ignore_file, mode="w") as gitignore:
            gitignore.write(f"{self.SHELF_FILE_NAME}*")

    def _create_mitigation_branch(
        self, conflict_info: Conflict, branch_name: str, mitigation_func: str
    ):
        self.repo.create_head(branch_name).checkout()

        self.conflict_handler.render(
            dirname=self.config_path,
            conflict=conflict_info,
            mitigation_func=mitigation_func,
        )

        self.repo.git.add(u=True)
        self.repo.index.commit(branch_name)

    def get_mitigation_branches(self):
        return set(self.repo.heads).difference(
            {self.repo.heads.master, self.repo.heads.initial}
        )

    def remove_mitigations_branches(self):
        mitigations_branch_to_remove = self.get_mitigation_branches()
        if mitigations_branch_to_remove:
            log.info(f"Removing stale branches: {mitigations_branch_to_remove}")
            for head in mitigations_branch_to_remove:
                head.delete(self.repo, head, force=True)

    @staticmethod
    def _mitigation_is_recommended(conflict_info: Conflict, mitigation: str):
        current_mitigation = conflict_info.mitigations["mitigations"][mitigation]
        recommended_mitigation = conflict_info.mitigations["recommended"]
        return current_mitigation.__name__ == recommended_mitigation.__name__
