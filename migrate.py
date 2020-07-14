import click

from journeys.config import Config
from journeys.modifier.dependency import build_dependency_map
from journeys.parser import build
from journeys.parser import lex
from journeys.parser import parse
from journeys.utils.image import get_image_from_ucs_reader
from journeys.utils.ucs_ops import tar_file
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
    click.echo("\n")
    ucs_reader = UcsReader(extracted_ucs_dir=output_dir)
    click.echo(f"Your hardware is: {ucs_reader.get_ucs_platform()}")
    click.echo(f"Software Version: \n{ucs_reader.get_version_file()}")

    click.echo(get_image_from_ucs_reader(ucs_reader=ucs_reader))
    click.echo(ucs_reader.get_bigdb_variable(key="Cluster.MgmtIpaddr", option="type"))

    new_ucs = tar_file(archive_file="new_example.ucs", input_dir=output_dir)
    click.echo(f"New ucs location {new_ucs}")


@cli.command()
@click.argument("config-filename")
def find_lexers(config_filename):
    click.echo(lex(filename=config_filename))


@cli.command()
@click.argument("config-filename")
def parse_config(config_filename):
    click.echo(parse(filename=config_filename, out=config_filename + ".json", indent=2))


@cli.command()
@click.argument("config-filename")
def build_config(config_filename):
    click.echo(build(filename=config_filename))


@cli.command()
@click.argument("config-filename")
def build_dependency_tree(config_filename):

    config = Config.from_conf(filename=config_filename)
    _ = build_dependency_map(config)


if __name__ == "__main__":
    cli()
