import click

from scf_tool.SCFStateMachine import SCFStateMachine

from parser import parse_file
from utils.ucs_ops import tar_file
from utils.ucs_ops import untar_file
from utils.ucs_reader import UcsReader
from utils.image import get_image_from_ucs_reader
from parser import lex
from parser import parse
from parser import build


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
    output_dir = untar_file(ucs_filename, dir='/tmp')
    click.echo(f"Ucs was unpacked in: {output_dir}")
    click.echo("\n")
    ucs_reader = UcsReader(extracted_ucs_dir=output_dir)
    click.echo(f"Your hardware is: {ucs_reader.get_ucs_platform()}")
    click.echo(f"Software Version: \n{ucs_reader.get_version_file()}")
    tar_file(archive_file='new_example.ucs', input_dir=output_dir)
    click.echo(get_image_from_ucs_reader(ucs_reader=ucs_reader))

    click.echo(lex(filename='bigip_nginx.conf'))


@cli.command()
@click.argument("config-filename")
def find_lexers(config_filename):
    click.echo(lex(filename=config_filename))


@cli.command()
@click.argument("config-filename")
def parse_config(config_filename):
    click.echo(parse(filename=config_filename, out=config_filename + '.json', indent=2))


@cli.command()
@click.argument("config-filename")
def build_config(config_filename):
    click.echo(build(filename=config_filename))


@cli.command()
@click.argument("config_file")
def parse_config_scf(config_file):
    """ Parse config file and print its contents"""

    with open(config_file, "r") as f:
        buffer = f.read()

    machine = SCFStateMachine(source=buffer)
    output = machine.run()

    for o in output:
        print(str(o))
        print('==============')


# TODO: Remove once not needed
@cli.command()
@click.argument("config_file")
def compare_scf_crossplane(config_file):
    """ Parse config file with SCF and Crossplane and compare results"""

    with open(config_file, "r") as f:
        buffer = f.read()

    machine = SCFStateMachine(source=buffer)
    output_scf = machine.run()
    list_scf = [
        {
            "index": idx,
            "module": obj.objmodule,
            "type": " ".join(obj.objtype),
            "name": obj.objname.split('"')[1] if obj.objname and obj.objname.startswith('"') else obj.objname
        } for idx, obj in enumerate(output_scf)
    ]


    kwargs = {
        'catch_errors': None,
        'ignore': [],
        'comments': False,
        'strict': False
    }

    result_crossplane = parse_file(
        filename = config_file,
        **kwargs
    )
    output_crossplane = result_crossplane['config'][0]['parsed']
    list_crossplane = [
        {
            "index": idx,
            "module": obj["directive"],
            "type": obj["type"],
            "name": obj["name"]
        } for idx, obj in enumerate(output_crossplane)
    ]

    print(f'Number of objects: scf={len(list_scf)}, parser={len(list_crossplane)}')

    idx = -1
    failure = False
    while True:
        idx += 1
        if idx + 1 > len(list_scf) or idx + 1 > len(list_crossplane):
            break
        scf = list_scf[idx]
        crossplane = list_crossplane[idx]

        if scf == crossplane:
            continue

        failure = True
        print(
            f'Found difference in object no {idx}:\n'
            f'\tscf={scf}\n'
            f'\tparser={crossplane}'
        )

    if failure:
        import sys
        sys.exit(1)


if __name__ == '__main__':
    cli()
