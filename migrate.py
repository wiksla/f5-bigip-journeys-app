import click
import json

from utils.ucs_handler import obtain_data_from_host
from parser.obtain_data import obtain_guests_data


@click.group()
def cli():
    """
    Tool useful in config migration process: \n
        * CBIP VCMP(guest) to VELOS(tenant).
    """
    pass


@cli.command()
@click.argument("host")
def list_all_guests(host):
    """ List all guest available in  host configuration. """
    guests_data = obtain_data_from_host(ucs_fn=host, obtain=obtain_guests_data)

    click.echo("Host config contains guests: ")
    for idx, guest in enumerate(guests_data.keys(), start=1):
        click.echo("[{}]: {}".format(idx, guest))


@cli.command()
@click.option("--name", help="Specific guest name. ", default="all_")
@click.argument("host")
def guest_info(host, name):
    """  Obtain all tenant requirement based on VCMP(host)."""

    guests_data = obtain_data_from_host(ucs_fn=host, obtain=obtain_guests_data)
    if name == "all_":
        click.echo("Number of guests: {}".format(len(guests_data.keys())))
        click.echo("All guest configuration data: ")
        click.echo(json.dumps(guests_data, indent=4))
    else:
        click.echo("Guest name: {}".format(name))
        click.echo(json.dumps(guests_data[name], indent=4))


@cli.command()
@click.argument("guest")
def migrate(guest):
    """  Making guest config loadable on VELOS (tenant). """
    click.echo("Convert ucs to be loadable on VELOS tenant: {}".format(guest))


if __name__ == "__main__":
    cli()
