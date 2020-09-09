#!/usr/bin/env python
import json
import os
import random
import string
from contextlib import contextmanager

import click
from git.exc import GitError

from journeys.controller import MigrationController
from journeys.errors import AlreadyInitializedError
from journeys.errors import ArchiveDecryptError
from journeys.errors import ArchiveOpenError
from journeys.errors import ConflictNotResolvedError
from journeys.errors import DifferentConflictError
from journeys.errors import NotAllConflictResolvedError
from journeys.errors import NotInitializedError
from journeys.errors import NotMasterBranchError
from journeys.errors import UnknownConflictError
from journeys.utils.device import Device
from journeys.utils.device import delete_file
from journeys.utils.device import get_image
from journeys.utils.device import get_ucs
from journeys.utils.device import save_ucs
from journeys.utils.resource_check import (
    ensure_if_minimum_resources_are_met_on_destination,
)
from journeys.validators.comparers import compare_db
from journeys.validators.comparers import compare_memory_footprint
from journeys.validators.comparers import tmsh_compare
from journeys.validators.core_watcher import list_cores
from journeys.validators.deployment import get_mcp_status
from journeys.validators.deployment import get_tmm_global_status
from journeys.validators.deployment import wait_for_prompt_state
from journeys.validators.ltm_checks import get_ltm_vs_status


@click.group()
def cli():
    """
    Tool useful in config migration process: \n
        * CBIP to VELOS(tenant).
    """
    pass


def print_conflicts_info(conflicts):
    click.echo("There are following conflicts waiting to be resolved:")
    for _id, conflict in conflicts.items():
        click.echo("")
        click.echo(f"{conflict.id}:")
        conflict_name = conflict.id
        for line in conflict.summary:
            click.echo(f"\t{line}")
    click.echo("")
    click.echo("Please run 'journey.py resolve <Conflict>' to apply sample fixes.")
    click.echo(f"Example 'journey.py resolve {conflict_name}'")


def print_no_conflict_info(history):
    click.echo("No conflicts has been found.")
    click.echo("")
    click.echo("In order to generate output ucs run 'journey.py generate'")

    if not history:
        return

    click.echo("")
    click.echo(
        "In order to review the changes history run 'journey.py history' or 'journey.py history --details'"
    )


def print_conflict_resolution_help(conflict_info, working_directory, config_path):
    click.echo(f"Workdir: {working_directory}")
    click.echo(f"Config path: {config_path}\n")
    click.echo(f"Resolving conflict_info {conflict_info.id}\n")
    click.echo(
        f"Resolve the issues on objects commented with '{conflict_info.id}' in the following files:"
    )
    for filename in conflict_info.files_to_render:
        click.echo(f"\t{filename}")

    click.echo("")
    click.echo("Proposed mitigations are listed below:")
    for mitigation in conflict_info.mitigations:
        if mitigation == "comment_only":
            continue
        mitigation_name = f"{conflict_info.id}_{mitigation}"
        click.echo(f"\t{mitigation_name}")
    click.echo("")
    click.echo("To view the mitigation content, run 'journey.py show <mitigation>'")
    click.echo(f"Example 'journey.py show {mitigation_name}'")
    click.echo("")
    click.echo("To view the issues found, run 'journey.py diff'")
    click.echo("")
    click.echo(
        "To apply proposed changes right away run"
        "'journey.py cleanup ; journey.py use <mitigation>"
    )
    click.echo(f"Example 'journey.py cleanup ; journey.py use {mitigation_name}'")
    click.echo("")

    click.echo(
        "Alternatively, you can edit the files manually and run 'journey.py migrate'"
    )


@contextmanager
def error_handler():
    try:
        yield
    except AlreadyInitializedError as e:
        click.echo("Migration process has already been started.")
        click.echo(
            f"In order to start processing new ucs file run 'journey.py start {e.input} --clear'"
        )

    except ArchiveOpenError:
        click.echo("Failed to open the archive.")
        click.echo("")
        click.echo(
            "If the archive is encrypted rerun with --ucs-passphrase <passphrase> parameter."
        )

    except ArchiveDecryptError:
        click.echo("Failed to decrypt the archive.")
        click.echo("")
        click.echo("Make sure that appropriate passphrase was passed.")

    except NotMasterBranchError:
        click.echo("Please checkout to master branch.")

    except NotInitializedError:
        click.echo("The migration process has not been started yet.")
        click.echo("In order to start new Migration process run 'journey.py start'")

    except ConflictNotResolvedError as e:
        click.echo(f"Current conflict_info {e.conflict_id} is not yet resolved.")
        click.echo("")
        print_conflict_resolution_help(
            conflict_info=e.conflict_info,
            working_directory=e.working_directory,
            config_path=e.config_path,
        )

    except DifferentConflictError as e:
        click.echo(
            f"Conflict {e.conflict_id} resolution already in progress."
            "Finish it by calling 'journey.py migrate' first before starting a new one."
        )
    except UnknownConflictError as e:
        click.echo(
            f"Invalid conflict_info ID ({e.conflict_id}) - given conflict_info not found in the config."
        )
    except NotAllConflictResolvedError:
        click.echo("There still are some unresolved conflicts.")
        click.echo("")
        click.echo("In order to handle them run 'journey.py migrate'")


def process_and_print_output(controller: MigrationController):
    current_conflicts = controller.process()
    if current_conflicts:
        print_conflicts_info(conflicts=current_conflicts)
    else:
        print_no_conflict_info(history=controller.history)


@cli.command()
@click.argument("ucs")
@click.option("--clear", is_flag=True, help="Clear all work-in-progress data.")
@click.option("--ucs-passphrase", default="", help="Passphrase to decrypt ucs archive.")
def start(ucs, clear, ucs_passphrase):
    """ Start migration process. """
    with error_handler():
        controller = MigrationController(clear=clear, allow_empty=True)
        controller.initialize(input_ucs=ucs, ucs_passphrase=ucs_passphrase)
        process_and_print_output(controller=controller)


@cli.command()
@click.argument("ucs", default="")
def migrate(ucs):
    """ Continue or resume migration process. """
    # TODO: remove after release
    if ucs:
        click.echo("Ucs argument is deprecated.")
        click.echo("In order to start new Migration process run 'journey.py start'")

    with error_handler():
        controller = MigrationController()
        process_and_print_output(controller=controller)


@cli.command()
@click.argument("conflict_id")
def resolve(conflict_id):
    """ Start single conflict resolution process. """
    with error_handler():
        controller = MigrationController()
        conflict_info, working_directory, config_path = controller.resolve(
            conflict_id=conflict_id
        )
        print_conflict_resolution_help(
            conflict_info=conflict_info,
            working_directory=working_directory,
            config_path=config_path,
        )


@cli.command()
@click.argument("mitigation")
def show(mitigation):
    """ Show proposed mitigation for a conflict. """
    with error_handler():
        controller = MigrationController()
        repo = controller.repo
        current_conflict = controller.current_conflict
        if not current_conflict:
            click.echo("Not resolving any conflict_info at this point.")
            click.echo(
                "To start resolving process run 'journey.py resolve <conflict_id>'."
            )
            return
        try:
            click.echo(repo.git.show(mitigation))
        except GitError:
            click.echo("Given mitigation is not valid")


@cli.command()
def diff():
    """ Show changes made or conflict highlights. """
    with error_handler():
        controller = MigrationController()
        repo = controller.repo
        click.echo(repo.git.diff())


@cli.command()
@click.argument("mitigation")
def use(mitigation):
    """ Apply proposed mitigation. """
    with error_handler():
        controller = MigrationController()
        repo = controller.repo
        current_conflict = controller.current_conflict
        if not current_conflict:
            click.echo("Not resolving any conflict_info at this point.")
            click.echo(
                "To start resolving process run 'journey.py resolve <conflict_id>'."
            )
            return

        if repo.is_dirty():
            click.echo(
                "Local changes detected. Clean it before using one of provided mitigations"
            )
            click.echo("To clean local changes run 'journey.py cleanup'.")
            return
        try:
            repo.git.merge(mitigation)
            process_and_print_output(controller=controller)
        except GitError:
            click.echo("Given mitigation is not valid")


@cli.command()
def cleanup():
    """ Clean local changes. """
    with error_handler():
        controller = MigrationController()
        repo = controller.repo
        repo.git.checkout(".")


@cli.command()
@click.option("--details", is_flag=True, help="Print details of a conflict resolution.")
def history(details):
    """ Show conflict resolution history. """
    with error_handler():
        controller = MigrationController()
        repo = controller.repo
        commits_history = controller.history()

        if not commits_history:
            click.echo("No steps has been done so far.")
            return

        click.echo("So far, following steps was made:")
        for idx, commit in enumerate(commits_history):
            click.echo(f"\t{idx + 1}: {commit.summary}")
            if details:
                click.echo(repo.git.show(commit.hexsha))

        click.echo("")
        click.echo(
            "In order to revert conflict_info resolution run 'journey.py revert <step name>'."
        )
        click.echo("")
        click.echo(
            "Note that reverting a conflict_info resolution will revert all the subsequent resolutions."
        )


@cli.command()
@click.argument("step")
def revert(step):
    """ Revert conflict resolution. """
    with error_handler():
        controller = MigrationController()
        repo = controller.repo
        commits_history = controller.history()
        try:
            commit = [commit for commit in commits_history if commit.summary == step][0]
        except IndexError:
            click.echo("Given step was not found.")
            click.echo(
                "In order to list steps performed so far run 'journey.py history'"
            )
            return

        repo.git.reset(commit.parents[0])
        repo.git.checkout(".")
        process_and_print_output(controller=controller)


@cli.command()
@click.option(
    "--output", default="output.ucs", help="Use given filename instead of default."
)
@click.option("--ucs-passphrase", default="", help="Passphrase to encrypt ucs archive.")
@click.option(
    "--force",
    is_flag=True,
    help="Generate output ucs even if not all conflict_info has been resolved.",
)
def generate(output, ucs_passphrase, force):
    """ Generate output. """
    with error_handler():
        controller = MigrationController()
        output_ucs = controller.generate(
            force=force, output=output, ucs_passphrase=ucs_passphrase
        )
        click.echo(f"Output ucs has been stored as {output_ucs}.")


@cli.command(hidden=True)
def prompt():
    with error_handler():
        controller = MigrationController()
        click.echo(controller.prompt())


@cli.command()
@click.option("--host", required=True)
@click.option(
    "--username", default="root", help="Username to use when connecting host."
)
@click.option("--password", required=True, help="Password to use when connecting host.")
def resources(host, username, password):
    """ Check if destination has enough resources to migrate ucs. """
    with error_handler():
        controller = MigrationController()

        device = Device(host=host, ssh_username=username, ssh_password=password)
        click.echo(
            ensure_if_minimum_resources_are_met_on_destination(
                config_path=controller.repo_path, device=device
            )
        )


@cli.command()
@click.option("--host", required=True, help="Host to fetch ucs from.")
@click.option(
    "--username", default="root", help="Username to use when connecting host."
)
@click.option("--password", required=True, help="Password to use when connecting host.")
@click.option(
    "--ucs-passphrase", default=None, help="Passphrase to encrypt ucs archive."
)
@click.option("--output", default="ex.ucs", help="Output filename.")
def download_ucs(host, username, password, ucs_passphrase, output):
    """ Download ucs from live system. """
    if not ucs_passphrase:
        ucs_passphrase = "".join(
            random.choice(string.ascii_letters + string.digits) for i in range(10)
        )

    device = Device(host=host, ssh_username=username, ssh_password=password)
    version = get_image(device=device)

    click.echo(f"Version on bigip: {version}")

    if version.is_velos_supported():
        click.echo("BIGIP version is supported by VELOS.")
        ucs_remote_dir = save_ucs(
            device=device, ucs_name=output, ucs_passphrase=ucs_passphrase
        )

        working_directory = os.environ.get("MIGRATE_DIR", ".")
        local_ucs_path = get_ucs(
            device=device,
            remote=ucs_remote_dir,
            local_ucs_name=os.path.join(working_directory, output),
        )

        delete_file(device=device, location=ucs_remote_dir)
        click.echo(f"Downloaded ucs is available locally: {local_ucs_path.local} ")
        delete_file(device=device, location=ucs_remote_dir)
        click.echo(f"Downloaded ucs is available locally: {local_ucs_path.local}.")
        click.echo(f"It has been encrypted using passphrase '{ucs_passphrase}'.")
    else:
        click.echo("Migration process is not available for you BIGIP version.")


@cli.command()
@click.option("--source-host", required=True)
@click.option("--source-username", default="root")
@click.option("--source-password", required=True)
@click.option("--source-admin-username", default="admin")
@click.option("--source-admin-password", required=True)
@click.option("--destination-host", required=True)
@click.option("--destination-username", default="root")
@click.option("--destination-password", required=True)
@click.option("--destination-admin-username", default="admin")
@click.option("--destination-admin-password", required=True)
def diagnose(
    source_host,
    source_username,
    source_password,
    source_admin_username,
    source_admin_password,
    destination_host,
    destination_username,
    destination_password,
    destination_admin_username,
    destination_admin_password,
):

    source = Device(
        host=source_host,
        ssh_username=source_username,
        ssh_password=source_password,
        api_username=source_admin_username,
        api_password=source_admin_password,
    )
    destination = Device(
        host=destination_host,
        ssh_username=destination_username,
        ssh_password=destination_password,
        api_username=destination_admin_username,
        api_password=destination_admin_password,
    )

    mcp_status = get_mcp_status(bigip=destination)
    click.echo(f"MCPD status:\n{json.dumps(mcp_status, indent=4)}")
    if (
        not mcp_status["last-load"] == "full-config-load-succeed"
        and mcp_status["phase"] == "running"
    ):
        click.echo("MCP down")

    tmm_status = get_tmm_global_status(bigip=destination)
    click.echo(f"TMM status:\n{json.dumps(tmm_status, indent=4)}")
    if not wait_for_prompt_state(device=destination):
        click.echo("Prompt is not active/standby")

    click.echo(list_cores(device=destination, raise_exception=True))

    db_diff = compare_db(first=source, second=destination)
    click.echo(f"Sys DB diff:\n{db_diff.pretty()}")

    module_diff = compare_memory_footprint(first=source, second=destination)
    click.echo(f"Memory footprint diff:\n{module_diff.pretty()}")

    sample_tmsh_diff = tmsh_compare(
        cmd="tmsh show sys version", first=source, second=destination
    )
    click.echo(f"tmsh show sys version diff:\n{sample_tmsh_diff}")

    click.echo(get_ltm_vs_status(device=source))


if __name__ == "__main__":
    cli()
