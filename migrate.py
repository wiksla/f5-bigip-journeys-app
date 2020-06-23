import click
import json


@click.group()
def cli():
    """
    Tool useful in config migration process: \n
        * CBIP to VELOS(tenant).
    """
    pass


@cli.command()
@click.argument("guest")
def make_migrate(guest):
    """  Making CBIP config loadable on VELOS (tenant). """
    click.echo("Convert ucs to be loadable on VELOS tenant: {}".format(guest))


