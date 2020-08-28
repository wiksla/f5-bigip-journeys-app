#!/usr/bin/env python
import os

import click

from journeys.config import Config
from journeys.controller import MigrationController
from journeys.errors import ArchiveDecryptError
from journeys.errors import ArchiveOpenError
from journeys.errors import ConflictNotResolvedError
from journeys.errors import DifferentConflictError
from journeys.errors import DifferentUcsError
from journeys.errors import NotAllConflictResolvedError
from journeys.errors import NotMasterBranchError
from journeys.errors import UnknownConflictError
from journeys.modifier.dependency import DependencyMap
from journeys.parser import parse
from journeys.utils.device import Device


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
def migrate(ucs, clear, ucs_passphrase):

    controller = MigrationController(
        input_ucs=ucs, clear=clear, ucs_passphrase=ucs_passphrase
    )
    try:
        conflicts = controller.process()
        if conflicts:
            print_conflicts_info(conflicts)
        else:
            click.echo("No conflicts has been found in the given ucs.")
            click.echo("")
            click.echo("In order to generate output ucs run journey.py generate")

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

    except DifferentUcsError:
        click.echo("Different ucs file received as an input.")
        click.echo(
            f"In order to start processing new ucs file run journey.py migrate {ucs} --clear"
        )
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
            "Finish it first and call 'journey.py migrate' before starting a new one."
        )
    except UnknownConflictError:
        click.echo(
            f"Invalid conflict ID ({conflict})- given conflict not found in the config."
        )


@cli.command()
@click.option("--output", default="", help="Use given filename instead of default.")
@click.option("--ucs-passphrase", default="", help="Passphrase to encrypt ucs archive.")
@click.option(
    "--force",
    is_flag=True,
    help="Generate output ucs even if not all conflict has been resolved.",
)
def generate(output, ucs_passphrase, force):
    controller = MigrationController(output_ucs=output, ucs_passphrase=ucs_passphrase)

    try:
        output_ucs = controller.generate(force=force)
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
@click.option(
    "--password",
    prompt=True,
    hide_input=True,
    help="Password to use when connecting host.",
)
@click.option(
    "--ucs-passphrase", default=None, help="Passphrase to encrypt ucs archive."
)
@click.option("--output", default="ex.ucs", help="Output filename.")
def download_ucs(host, username, password, ucs_passphrase, output):
    device = Device(ip=host, username=username, password=password)
    version = device.get_image()

    click.echo(f"Version on bigip: {version}")

    if version.is_velos_supported():
        click.echo("BIGIP version is supported by VELOS.")
        ucs_remote_dir = device.save_ucs(ucs_name=output, ucs_passphrase=ucs_passphrase)

        working_directory = os.environ.get("MIGRATE_DIR", ".")
        local_ucs_path = device.get_ucs(
            remote=ucs_remote_dir,
            local_ucs_name=os.path.join(working_directory, output),
        )

        device.delete_ucs(ucs_location=ucs_remote_dir)
        click.echo(f"Downloaded ucs is available locally: {local_ucs_path.local} ")
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
    device = Device(ip=host, username=username, password=password)
    click.echo(device.obtain_source_resources())


@cli.command()
@click.argument("config-filename")
def build_dependency_tree(config_filename):

    config = Config.from_conf(filename=config_filename)
    _ = DependencyMap(config)


if __name__ == "__main__":
    cli()
