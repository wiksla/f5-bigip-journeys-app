#!/usr/bin/env python
import click

from journeys.config import Config
from journeys.controller import MigrationController
from journeys.modifier.dependency import build_dependency_map
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
def migrate(ucs, clear):
    controller = MigrationController(input_ucs=ucs, clear=clear,)
    controller.process()


@cli.command()
@click.argument("conflict")
def resolve(conflict):
    controller = MigrationController()
    controller.resolve(conflict_id=conflict)


@cli.command()
def prompt():
    controller = MigrationController()
    click.echo(controller.prompt())


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
