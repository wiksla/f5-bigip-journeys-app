#!/usr/bin/env python
import os

import click

from journeys.config import Config
from journeys.controller import MigrationController
from journeys.errors import ArchiveDecryptError
from journeys.errors import ArchiveOpenError
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


@cli.command()
@click.argument("ucs", default="")
@click.option("--clear", is_flag=True, help="Clear all work-in-progress data.")
@click.option("--ucs-passphrase", default="", help="Passphrase to decrypt ucs archive.")
def migrate(ucs, clear, ucs_passphrase):

    controller = MigrationController(
        input_ucs=ucs, clear=clear, ucs_passphrase=ucs_passphrase
    )
    try:
        controller.process()
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
@click.argument("conflict")
def resolve(conflict):
    controller = MigrationController()
    controller.resolve(conflict_id=conflict)


@cli.command()
@click.option("--output", default="", help="Use given filename instead of default.")
@click.option("--ucs-passphrase", default="", help="Passphrase to encrypt ucs archive.")
def generate(output, ucs_passphrase):
    controller = MigrationController(output_ucs=output, ucs_passphrase=ucs_passphrase)
    controller.generate()


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
@click.option("--password", required=True)
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
