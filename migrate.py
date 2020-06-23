import click
import json

from parser.SCFStateMachine import SCFStateMachine


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


@cli.command()
@click.argument("config_file")
def parse_config(config_file):
    """ Parse config file and print its contents"""

    with open(config_file, "r") as f:
        buffer = f.read()

    machine = SCFStateMachine(source=buffer)
    output = machine.run()

    for o in output:
        print(str(o))
        print('==============')


if __name__ == '__main__':
    cli()
