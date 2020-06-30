import click
import json

from parser.SCFStateMachine import SCFStateMachine

from crossplane.parser import parse as parse_file



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

    print(f'Number of objects: scf={len(list_scf)}, crossplane={len(list_crossplane)}')

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
            f'\tcrossplane={crossplane}'
        )

    if failure:
        import sys
        sys.exit(1)

if __name__ == '__main__':
    cli()
