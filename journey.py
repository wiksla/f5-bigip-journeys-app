#!/usr/bin/env python
import json
import os
import random
import string

import click

from journeys.config import Config
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
from journeys.modifier.dependency import DependencyMap
from journeys.parser import parse
from journeys.utils.device import Device
from journeys.utils.device import delete_ucs
from journeys.utils.device import get_image
from journeys.utils.device import get_ucs
from journeys.utils.device import obtain_source_resources
from journeys.utils.device import save_ucs
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
        for line in conflict.summary:
            click.echo(f"\t{line}")
    click.echo("")
    click.echo("Please run 'journey.py resolve <Conflict>' to apply sample fixes.")
    click.echo(f"Example 'journey.py resolve {next(iter(conflicts.keys()))}'")


def print_no_conflict_info():
    click.echo("No conflicts has been found.")
    click.echo("")
    click.echo("In order to generate output ucs run journey.py generate")


def print_conflict_resolution_help(controller, conflict):
    click.echo(f"Workdir: {controller.working_directory}")
    click.echo(f"Config path: {controller.config_path}\n")
    click.echo(f"Resolving conflict {conflict.id}\n")
    click.echo(
        f"Resolve the issues on objects commented with '{conflict.id}' in the following files:"
    )
    for filename in conflict.files_to_render:
        click.echo(f"\t{filename}")

    click.echo("")
    click.echo(
        f"Proposed fixes are present in branches (in git repository: {controller.repo_path}):"
    )
    for mitigation in conflict.mitigations:
        if mitigation == "comment_only":
            continue

        click.echo(f"\t{conflict.id}_{mitigation}")
    click.echo("")
    click.echo(
        f"To view the issues found, enter the {controller.repo_path} directory and check the diff of the current branch"
        f" (e.g. 'git diff')"
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


@cli.command()
@click.argument("ucs", default="")
@click.option("--clear", is_flag=True, help="Clear all work-in-progress data.")
@click.option("--ucs-passphrase", default="", help="Passphrase to decrypt ucs archive.")
def start(ucs, clear, ucs_passphrase):
    controller = MigrationController(clear=clear)
    try:
        controller.initialize(input_ucs=ucs, ucs_passphrase=ucs_passphrase)
        conflicts = controller.process()
        if conflicts:
            print_conflicts_info(conflicts)
        else:
            print_no_conflict_info()

    except AlreadyInitializedError:
        click.echo("Migration process has already been started.")
        click.echo(
            f"In order to start processing new ucs file run journey.py start {ucs} --clear"
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


@cli.command()
@click.argument("ucs", default="")
def migrate(ucs):

    # TODO: remove after release
    if ucs:
        click.echo("Ucs argument is deprecated.")
        click.echo("In order to start new Migration process run journey.py start")

    controller = MigrationController()

    try:
        conflicts = controller.process()
        if conflicts:
            print_conflicts_info(conflicts)
        else:
            print_no_conflict_info()

    except NotMasterBranchError:
        click.echo("Please checkout to master branch.")

    except NotInitializedError:
        click.echo("The migration process has not been started yet.")
        click.echo("In order to start new Migration process run journey.py start")

    except ConflictNotResolvedError as e:
        click.echo(f"ERROR: Current conflict {e.conflict_id} is not yet resolved.")
        click.echo("")
        print_conflict_resolution_help(controller, e.conflict_info)


@cli.command()
@click.argument("conflict")
def resolve(conflict):
    controller = MigrationController()
    try:
        conflict_info = controller.resolve(conflict_id=conflict)
        print_conflict_resolution_help(controller, conflict_info)
    except DifferentConflictError as e:
        click.echo(
            f"Conflict {e.conflict_id} resolution already in progress."
            "Finish it by calling 'journey.py migrate' first before starting a new one."
        )
    except UnknownConflictError:
        click.echo(
            f"Invalid conflict ID ({conflict})- given conflict not found in the config."
        )


@cli.command()
@click.option(
    "--output", default="output.ucs", help="Use given filename instead of default."
)
@click.option("--ucs-passphrase", default="", help="Passphrase to encrypt ucs archive.")
@click.option(
    "--force",
    is_flag=True,
    help="Generate output ucs even if not all conflict has been resolved.",
)
def generate(output, ucs_passphrase, force):
    controller = MigrationController()

    try:
        output_ucs = controller.generate(
            force=force, output=output, ucs_passphrase=ucs_passphrase
        )
        click.echo(f"Output ucs has been stored as {output_ucs}.")
    except NotMasterBranchError:
        click.echo("Please checkout to master branch.")
    except NotAllConflictResolvedError:
        click.echo("There still are some unresolved conflicts.")
        click.echo("")
        click.echo("In order to handle them run journey.py migrate")


@cli.command()
def prompt():
    controller = MigrationController()
    click.echo(controller.prompt())


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

        delete_ucs(device=device, ucs_location=ucs_remote_dir)
        click.echo(f"Downloaded ucs is available locally: {local_ucs_path.local} ")
        delete_ucs(device=device, ucs_location=ucs_remote_dir)
        click.echo(f"Downloaded ucs is available locally: {local_ucs_path.local}.")
        click.echo(f"It has been encrypted using passphrase '{ucs_passphrase}'.")
    else:
        click.echo("Migration process is not available for you BIGIP version.")


@cli.command()
@click.argument("config-filename")
def parse_config(config_filename):
    click.echo(parse(filename=config_filename, out=config_filename + ".json", indent=2))


@cli.command()
@click.option("--host", required=True)
@click.option("--username", default="root")
@click.option(
    "--password",
    prompt=True,
    hide_input=True,
    help="Password to use when connecting host.",
)
def minimal_required_tenant_resources(host, username, password):
    device = Device(host=host, ssh_username=username, ssh_password=password)
    click.echo(obtain_source_resources(device=device))


@cli.command()
@click.argument("config-filename")
def build_dependency_tree(config_filename):

    config = Config.from_conf(filename=config_filename)
    _ = DependencyMap(config)


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
