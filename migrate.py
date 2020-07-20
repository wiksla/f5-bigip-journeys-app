import os

import click

from journeys.config import Config
from journeys.modifier.conflict.handler import ConflictHandler
from journeys.modifier.dependency import build_dependency_map
from journeys.parser import parse
from journeys.utils.device import Device
from journeys.utils.ucs_ops import untar_file
from journeys.utils.ucs_reader import UcsReader


@click.group()
def cli():
    """
    Tool useful in config migration process: \n
        * CBIP to VELOS(tenant).
    """
    pass


@cli.command()
@click.argument("ucs-filename")
def make_migration(ucs_filename):
    """  Making CBIP config loadable on VELOS (tenant). """
    click.echo(f"Convert ucs to be loadable on VELOS tenant: {ucs_filename}")
    output_dir = untar_file(ucs_filename, dir="/tmp")
    click.echo(f"Ucs was unpacked in: {output_dir}")
    ucs_reader = UcsReader(extracted_ucs_dir=output_dir)

    click.echo(f"BIGIP hardware version is: {ucs_reader.get_platform()}")

    version = ucs_reader.get_version()
    click.echo(f"BIGIP version is: {version.sequence}")

    if not version.is_velos_supported():
        click.echo(f"BIGIP {version.sequence} is not supported by VELOS.")
        return

    config: Config = ucs_reader.get_config()

    conflict_handler = ConflictHandler(config)
    conflicts = conflict_handler.detect_conflicts()

    conflicts_dir = os.path.join(output_dir, "conflicts")

    click.echo(f"Conflicts dir {conflicts_dir}")

    for conflict in conflicts:
        conflict_handler.render(
            dirname=os.path.join(conflicts_dir, conflict.id), conflict=conflict
        )

    click.echo("Resolve Conflict")


@cli.command()
@click.option("--host", required=True)
@click.option("--password", required=True)
def download_ucs(host, password):
    device = Device(ip=host, root_password=password)
    version = device.get_image()

    click.echo(f"Version on bigip: {version}")

    if version.is_velos_supported():
        click.echo("BIGIP version is supported by VELOS.")
        ucs_remote_dir = device.save_ucs(ucs_name="ex.ucs")
        local_ucs_path = device.get_ucs(
            remote=ucs_remote_dir, local_ucs_name="./ex.ucs"
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
@click.option("--password", required=True)
def minimal_required_tenant_resources(host, password):
    device = Device(ip=host, root_password=password)
    click.echo(device.obtain_source_resources())


@cli.command()
@click.argument("config-filename")
def build_dependency_tree(config_filename):

    config = Config.from_conf(filename=config_filename)
    _ = build_dependency_map(config)


if __name__ == "__main__":
    cli()
