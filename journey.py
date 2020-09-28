#!/usr/bin/env python
import logging
import os
import random
import string
import sys
from contextlib import contextmanager
from time import gmtime
from time import strftime

import click
from git.exc import GitError

from journeys import __version__ as journey_version
from journeys.controller import MigrationController
from journeys.errors import AlreadyInitializedError
from journeys.errors import ArchiveDecryptError
from journeys.errors import ArchiveOpenError
from journeys.errors import AS3InputDoesNotExistError
from journeys.errors import ConflictNotResolvedError
from journeys.errors import DeviceAuthenticationError
from journeys.errors import DifferentConflictError
from journeys.errors import LocalChangesDetectedError
from journeys.errors import NetworkConnectionError
from journeys.errors import NotAllConflictResolvedError
from journeys.errors import NotInitializedError
from journeys.errors import NotMasterBranchError
from journeys.errors import OutputAlreadyExistsError
from journeys.errors import UnknownConflictError
from journeys.modifier.conflict.plugins import load_plugins
from journeys.utils.device import REMOTE_UCS_DIRECTORY
from journeys.utils.device import Device
from journeys.utils.device import delete_file
from journeys.utils.device import format_restore_backup_command
from journeys.utils.device import format_ucs_load_command
from journeys.utils.device import get_file
from journeys.utils.device import get_image
from journeys.utils.device import load_ucs
from journeys.utils.device import put_file
from journeys.utils.device import save_ucs
from journeys.utils.resource_check import (
    ensure_if_minimum_resources_are_met_on_destination,
)
from journeys.validators.checks_for_cli import FAILED
from journeys.validators.checks_for_cli import auto_checks
from journeys.validators.checks_for_cli import default_checks
from journeys.validators.checks_for_cli import exclude_checks
from journeys.validators.checks_for_cli import run_diagnose
from journeys.validators.deployment import run_backup
from journeys.validators.exceptions import JourneysError
from journeys.workdir import WORKDIR

log = logging.getLogger(__name__)


def setup_logging(level=logging.DEBUG):
    log_file = os.path.join(WORKDIR, "journeys.log")

    format_string = "%(asctime)s %(name)s [%(levelname)s] %(message)s"
    formatter = logging.Formatter(format_string)

    handler = logging.FileHandler(log_file)
    handler.setLevel(level)
    handler.setFormatter(formatter)

    _log = logging.getLogger()
    _log.setLevel(level)
    _log.addHandler(handler)


@click.group()
@click.version_option(
    version=journey_version, message=f"Journey App Version: {journey_version}"
)
def cli():
    """
    Tool useful in config migration process: \n
        * CBIP to VELOS(tenant).\n
            - CBIP UCS files from 11.5.0 or higher versions are supported only\n
            - CBIP Source UCS version cannot be higher than VELOS tenant BIG-IP version\n
    Run 'journey.py features' and 'journey.py prerequisites' to get useful information
    before staring the migration process.
    """
    setup_logging()
    log.info(f"Processing command: {sys.argv}")


@cli.command()
def features():
    """ Prints a list of supported features """

    plugins = load_plugins()
    click.echo("Supported plugins are:")
    for plugin in plugins:
        click.echo(f"\t{plugin.ID}")


@cli.command()
def prerequisites():
    """ Prints prerequisites before start """

    click.echo(
        "Before start of migration process it is important to handle the master-key migration."
    )
    click.echo("It can be done in 2 following ways:")
    click.echo(
        "\t1. Copying Source System master key to the Destination System with 'f5mku' (recommended):"
    )
    click.echo("\t\tRun 'f5mku -K' on the Source System and copy the output.")
    click.echo("\t\tIt should look like this 'oruIVCHfmVBnwGaSR/+MAA=='.")
    click.echo("\t\tRun 'f5mku -r <copied value> on the Destination System.")
    click.echo("")
    click.echo("\t2. Reset the master key on Source System before saving the UCS:")
    click.echo(
        "\t\tRun 'tmsh modify sys crypto master-key prompt-for-password' on Source System."
    )
    click.echo(
        "\t\tInput password (remember it because it will be needed on the Destination System)."
    )
    click.echo(
        "\t\tSave master key change by running 'tmsh save sys config' on Source System."
    )
    click.echo(
        "\t\tRun 'tmsh modify sys crypto master-key prompt-for-password' on Destination System."
    )
    click.echo("\t\tInput remembered password from Source System.")
    click.echo(
        "\t\tSave master key change by running 'tmsh save sys config' on Destination System."
    )
    click.echo("")
    click.echo("\tMore details can be found here:")
    click.echo(
        "\t\t- K82540512: Overview of the UCS archive 'platform-migrate' option."
    )
    click.echo("\t\t  https://support.f5.com/csp/article/K82540512#p1")
    click.echo(
        "\t\t- K9420: Installing UCS files containing encrypted passwords or passphrases (11.5.x and later)"
    )
    click.echo("\t\t  https://support.f5.com/csp/article/K9420")
    click.echo("")

    click.echo("SSH public keys migration")
    click.echo(
        "\tSSH public keys for passwordless authentication may stop work after UCS migration."
    )
    click.echo("\tUCS file may not contain SSH public keys for users.")
    click.echo("\tIf the version is affected by the problem then:")
    click.echo(
        "\t\t- all keys files have to be migrated manually from source system to the target system"
    )
    click.echo(
        "\t\t- /etc/ssh directory has to be added to the UCS backup configuration od the source system"
    )
    click.echo(
        "\tFor more details how to manually mmimgrate SSH keys"
        " and to verify if your version is affected by the problem please read:"
    )
    click.echo(
        "\t\t- K22327083: UCS backup files do not include the /etc/ssh/ directory"
    )
    click.echo("\t\t  https://support.f5.com/csp/article/K22327083")
    click.echo(
        "\t\t- K17318: Public key SSH authentication may fail after installing a UCS"
    )
    click.echo("\t\t  https://support.f5.com/csp/article/K17318")
    click.echo(
        "\t\t- K13454: Configuring SSH public key authentication on BIG-IP systems (11.x - 15.x)"
    )
    click.echo("\t\t  https://support.f5.com/csp/article/K13454")
    click.echo("")

    print_destination_system_prerequisites()


@cli.command()
@click.argument("ucs")
@click.option("--clear", is_flag=True, help="Clear all work-in-progress data.")
@click.option("--ucs-passphrase", default="", help="Passphrase to decrypt ucs archive.")
@click.option(
    "--as3-path",
    help="Path to the AS3 declaration corresponding to this configuration.",
)
def start(ucs, clear, ucs_passphrase, as3_path):
    """ Start migration process. """
    with error_handler():
        controller = MigrationController(
            working_directory=WORKDIR, clear=clear, allow_empty=True
        )
        controller.initialize(
            input_ucs=ucs, ucs_passphrase=ucs_passphrase, as3_path=as3_path
        )
        version = controller.ucs_reader.get_version()
        if not version.is_velos_supported():
            click.echo(
                f"Migration from the provided ucs version {version.version} is not supported."
            )
            return
        process_and_print_output(controller=controller)


@cli.command()
@click.argument("ucs", default="")
@click.option("--message", default=None, help="Subject for local changes made.")
def migrate(ucs, message):
    """ Continue or resume migration process. """
    # TODO: remove after release
    if ucs:
        click.echo("Ucs argument is deprecated.")
        click.echo("In order to start new Migration process, run 'journey.py start'")

    with error_handler():
        controller = MigrationController(working_directory=WORKDIR)
        process_and_print_output(controller=controller, commit_name=message)


@cli.command()
@click.argument("conflict_id")
def resolve(conflict_id):
    """ Start single conflict resolution process. """
    with error_handler():
        controller = MigrationController(working_directory=WORKDIR)
        (
            conflict_info,
            working_directory,
            config_path,
            mitigation_branches,
        ) = controller.resolve(conflict_id=conflict_id)
        print_conflict_resolution_help(
            conflict_info=conflict_info,
            working_directory=working_directory,
            config_path=config_path,
            mitigation_branches=mitigation_branches,
        )


@cli.command()
def resolve_all():
    """ Resolve all conflicts with f5 recommended solutions. """
    with error_handler():
        controller = MigrationController(working_directory=WORKDIR)
        controller.resolve_recommended()
        print_no_conflict_info(history=controller.history)


@cli.command()
@click.argument("mitigation")
def show(mitigation):
    """ Show proposed mitigation for a conflict. """
    with error_handler():
        controller = MigrationController(working_directory=WORKDIR)
        repo = controller.repo
        current_conflict = controller.current_conflict
        if not current_conflict:
            click.echo("Not resolving any conflict_info at this point.")
            click.echo(
                "To start resolving process, run 'journey.py resolve <conflict_id>'."
            )
            return
        try:
            click.echo(repo.git.show(mitigation))
        except GitError:
            click.echo("Given mitigation is not valid")


@cli.command()
def diff():
    """ Show changes made or conflict highlights. """
    with error_handler():
        controller = MigrationController(working_directory=WORKDIR)
        repo = controller.repo
        click.echo(repo.git.diff())


@cli.command()
@click.argument("mitigation")
def use(mitigation):
    """ Apply proposed mitigation. """
    with error_handler():
        controller = MigrationController(working_directory=WORKDIR)
        repo = controller.repo
        repo.git.checkout(".")
        current_conflict = controller.current_conflict
        if not current_conflict:
            click.echo("Not resolving any conflict_info at this point.")
            click.echo(
                "To start resolving process, run 'journey.py resolve <conflict_id>'."
            )
            return

        if repo.is_dirty():
            click.echo(
                "Local changes detected. Clean it before using one of provided mitigations"
            )
            click.echo("To clean local changes, run 'journey.py cleanup'.")
            return
        try:
            repo.git.merge(mitigation)
            process_and_print_output(controller=controller)
        except GitError:
            click.echo("Given mitigation is not valid")


@cli.command()
def cleanup():
    """ Clean local changes. """
    with error_handler():
        controller = MigrationController(working_directory=WORKDIR)
        repo = controller.repo
        repo.git.checkout(".")


@cli.command()
@click.option("--details", is_flag=True, help="Print details of a conflict resolution.")
def history(details):
    """ Show conflict resolution history. """
    with error_handler():
        controller = MigrationController(working_directory=WORKDIR)
        repo = controller.repo
        commits_history = controller.history()

        if not commits_history:
            click.echo("No steps has been done so far.")
            return

        click.echo("So far, following steps were made:")
        for idx, commit in enumerate(commits_history):
            click.echo(f"\t{idx + 1}: {commit.summary}")
            if details:
                click.echo(repo.git.show(commit.hexsha))

        click.echo("")
        click.echo(
            "In order to revert conflict_info resolution, run 'journey.py revert <step name>'."
        )
        click.echo("")
        click.echo(
            "Note that reverting a conflict_info resolution will also revert all the subsequent resolutions."
        )


@cli.command()
@click.argument("step")
def revert(step):
    """ Revert conflict resolution. """
    with error_handler():
        controller = MigrationController(working_directory=WORKDIR)
        repo = controller.repo
        commits_history = controller.history()
        try:
            commit = [commit for commit in commits_history if commit.summary == step][0]
        except IndexError:
            click.echo("Given step was not found.")
            click.echo(
                "In order to list steps performed so far, run 'journey.py history'"
            )
            return

        repo.git.reset(commit.parents[0])
        repo.git.checkout(".")
        process_and_print_output(controller=controller)


@cli.command()
@click.option("--output", default=None, help="Use given filename instead of default.")
@click.option("--ucs-passphrase", default="", help="Passphrase to encrypt ucs archive.")
@click.option(
    "--output-as3", default=None, help="Use given filename instead of default for as3."
)
@click.option(
    "--force",
    is_flag=True,
    help="Generate output ucs even if not all conflict_info have been resolved.",
)
@click.option(
    "--overwrite",
    is_flag=True,
    help="Generate output ucs even if file with given name already exists.",
)
def generate(output, ucs_passphrase, output_as3, force, overwrite):
    """ Generate output UCS. """
    if not ucs_passphrase:
        ucs_passphrase = "".join(
            random.choice(string.ascii_letters + string.digits) for i in range(10)
        )

    with error_handler():
        controller = MigrationController(working_directory=WORKDIR)
        output_ucs_path, output_as3_path = controller.generate(
            output_ucs=output,
            ucs_passphrase=ucs_passphrase,
            output_as3=output_as3,
            force=force,
            overwrite=overwrite,
        )
        output_ucs_name = os.path.basename(output_ucs_path)

        click.echo(f"Output ucs has been stored as {output_ucs_path}.")
        click.echo(f"It has been encrypted using passphrase '{ucs_passphrase}'.")
        if output_as3_path:
            click.echo("")
            click.echo(f"Output as3 has been stored as {output_as3_path}.")

        click.echo("")
        click.echo("In order to deploy it on destination system, run")
        click.echo(
            f"'journey.py deploy --input-ucs {output_ucs_name} --ucs-passphrase {ucs_passphrase} "
            "--destination-host <host> --destination-username <username> --destination-password <password> "
            "--destination-admin-username <admin user> --destination-admin-password <admin password>'."
        )
        click.echo("Run 'journey.py deploy --help' for more details.")
        click.echo("")
        click.echo(
            f"In order to deploy the ucs manually, upload generated output to '{REMOTE_UCS_DIRECTORY}'"
            "on destination system."
        )
        click.echo(
            f"and run '{format_ucs_load_command(ucs=output_ucs_name, ucs_passphrase=ucs_passphrase)}'."
        )
        click.echo("")
        print_destination_system_prerequisites()


@cli.command(hidden=True)
def prompt():
    with error_handler():

        try:
            controller = MigrationController(working_directory=WORKDIR)
            prompt = controller.prompt()
        except NotInitializedError:
            prompt = "Not started"

        click.echo(f"\\e[1;32mjourney({prompt}): \\e[0m")


@cli.command()
@click.option("--host", required=True)
@click.option(
    "--username", default="root", help="Username to use when connecting to a host."
)
@click.option(
    "--password", required=True, help="Password to use when connecting to a host."
)
def resources(host, username, password):
    """ Check if destination has enough resources to migrate ucs. """
    with error_handler():
        controller = MigrationController(working_directory=WORKDIR)

        device = Device(host=host, ssh_username=username, ssh_password=password)
        click.echo(
            ensure_if_minimum_resources_are_met_on_destination(
                config_path=controller.repo_path, device=device
            )
        )


@cli.command()
@click.option("--host", required=True, help="Host to fetch ucs from.")
@click.option(
    "--username", default="root", help="Username to use when connecting to a host."
)
@click.option(
    "--password", required=True, help="Password to use when connecting to a host."
)
@click.option(
    "--ucs-passphrase", default=None, help="Passphrase to encrypt ucs archive."
)
@click.option("--output", default="ex.ucs", help="Output filename.")
def download_ucs(host, username, password, ucs_passphrase, output):
    """ Download ucs from live system. """
    if not ucs_passphrase:
        ucs_passphrase = "".join(
            random.choice(string.ascii_letters + string.digits) for i in range(10)
        )

    device = Device(host=host, ssh_username=username, ssh_password=password)
    version = get_image(device=device)

    click.echo(f"Version on BIG-IP: {version}")

    if version.is_velos_supported():
        click.echo("BIG-IP version is supported by VELOS.")
        ucs_remote_dir = save_ucs(
            device=device, ucs_name=output, ucs_passphrase=ucs_passphrase
        )

        local_ucs_path = get_file(
            device=device, remote=ucs_remote_dir, local=os.path.join(WORKDIR, output),
        )

        delete_file(device=device, remote=ucs_remote_dir)
        click.echo(f"Downloaded ucs is available locally: {local_ucs_path.local}.")
        click.echo(f"It has been encrypted using passphrase '{ucs_passphrase}'.")
    else:
        click.echo("Migration process is not available for your BIG-IP version.")


@cli.command()
@click.option(
    "--ucs-passphrase", default=None, help="Passphrase to decrypt ucs archive."
)
@click.option("--destination-host", required=True)
@click.option("--destination-username", default="root")
@click.option("--destination-password", required=True)
def backup(
    ucs_passphrase, destination_username, destination_host, destination_password
):
    """ Do a system backup. As Always. """
    destination = Device(
        host=destination_host,
        ssh_username=destination_username,
        ssh_password=destination_password,
    )
    try:
        backed_up = run_backup(destination, ucs_passphrase, is_user_triggered=True)
    except JourneysError as err:
        click.echo("\nBackup NOT created!!!\n")
        click.echo(err)  # TODO: replace with logger
        return
    restore_command = format_restore_backup_command(
        ucs=backed_up, ucs_passphrase=ucs_passphrase
    )
    click.echo(
        "Backup created.\n In case of emergency you can restore it on Destination System "
        "platform by running: \n "
        f"'{restore_command}'"
    )


@cli.command()
@click.option(
    "--ucs-passphrase", required=True, help="Passphrase to decrypt ucs archive."
)
@click.option("--autocheck", is_flag=True, help="Run diagnose option after deployment")
@click.option("--input-ucs", required=True, help="Filename for generated ucs file.")
@click.option("--destination-host", required=True)
@click.option("--destination-username", default="root")
@click.option("--destination-password", required=True)
@click.option("--destination-admin-username", default="admin")
@click.option("--destination-admin-password", required=True)
@click.option("--no-backup", is_flag=True, default=False, help="Skip auto backup.")
def deploy(
    input_ucs,
    ucs_passphrase,
    autocheck,
    destination_host,
    destination_username,
    destination_password,
    destination_admin_username,
    destination_admin_password,
    no_backup,
):
    """ Deploy UCS on Destination Platform. """

    if not os.path.exists(os.path.join(WORKDIR, input_ucs)):
        click.echo(f"Input file {input_ucs} does not exists.")
        return

    destination = Device(
        host=destination_host,
        ssh_username=destination_username,
        ssh_password=destination_password,
        api_username=destination_admin_username,
        api_password=destination_admin_password,
    )

    if no_backup:
        click.echo("Auto backup skipped by user.")
    else:
        try:
            backed_up = run_backup(
                destination, ucs_passphrase="", is_user_triggered=False
            )
            restore_command = format_restore_backup_command(
                ucs=backed_up, ucs_passphrase=""
            )
            click.echo(
                "Backup created.\n In case of emergency you can restore it on "
                "Destination Platform platform by running: \n"
                f"{restore_command}\n"
            )
        except JourneysError as err:
            click.echo("\nBackup NOT created!!!\n")
            log.debug(err)

    try:
        put_file(destination, os.path.join(WORKDIR, input_ucs), REMOTE_UCS_DIRECTORY)
        load_ucs(destination, input_ucs, ucs_passphrase)
    except JourneysError as c_err:
        click.echo(f"Failed to deploy ucs file! Encountered problem:\n" f"{c_err}")
        return

    check_success = True
    if autocheck:
        prefix = "autocheck_diagnose_output"
        timestamp = strftime("%Y%m%d%H%M%S", gmtime())
        output_log = os.path.join(WORKDIR, f"{prefix}_{timestamp}.log")
        output_json = os.path.join(WORKDIR, f"{prefix}_{timestamp}.json")
        with open(output_log, "w") as logfile:
            kwargs = {"destination": destination, "output": logfile}
            diagnose_result = run_diagnose(
                checks=auto_checks, kwargs=kwargs, output_json=output_json,
            )
        fails = []
        for check, result in diagnose_result.items():
            if result["result"] == FAILED:
                check_success = False
                fails.append(check)
        click.echo("Diagnose finished.")
        if check_success:
            click.echo("No known diagnose issues found.")
            click.echo(
                "To perform a self evaluation of the results, please check the output logs."
            )
        else:
            click.echo(
                f"Diagnose failures found in {', '.join(fails)}. Please check the output logs for details."
            )
    click.echo("")
    click.echo(
        f"Deployment completed {'successfully' if check_success else 'with errors'}."
    )


@cli.command()
@click.option("--source-host", required=True)
@click.option("--source-username", default="root")
@click.option("--source-password", required=True)
@click.option("--source-admin-username", default="admin")
@click.option("--source-admin-password", required=True)
@click.option("--destination-host", required=True)
@click.option("--destination-username", default="root")
@click.option("--destination-password", required=True)
@click.option("--destination-admin-username", default="admin")
@click.option("--destination-admin-password", required=True)
@click.option(
    "--excluded-checks",
    default="",
    help="Add checks to exclude in a list" 'e.g. \'["TMM status", "Core dumps"]\'',
)
def diagnose(
    source_host,
    source_username,
    source_password,
    source_admin_username,
    source_admin_password,
    destination_host,
    destination_username,
    destination_password,
    destination_admin_username,
    destination_admin_password,
    excluded_checks,
):
    """ Run diagnosis and comparison checks for Source and Destination Platforms. """
    source = Device(
        host=source_host,
        ssh_username=source_username,
        ssh_password=source_password,
        api_username=source_admin_username,
        api_password=source_admin_password,
    )
    destination = Device(
        host=destination_host,
        ssh_username=destination_username,
        ssh_password=destination_password,
        api_username=destination_admin_username,
        api_password=destination_admin_password,
    )
    prefix = "diagnose_output"
    timestamp = strftime("%Y%m%d%H%M%S", gmtime())
    output_log = os.path.join(WORKDIR, f"{prefix}_{timestamp}.log")
    output_json = os.path.join(WORKDIR, f"{prefix}_{timestamp}.json")

    if excluded_checks:
        try:
            checks = exclude_checks(default_checks, excluded_checks)
        except JourneysError as err:
            checks = default_checks
            log.debug(err)
    else:
        checks = default_checks

    with open(output_log, "w") as logfile:
        kwargs = {"destination": destination, "source": source, "output": logfile}
        run_diagnose(
            checks=checks, kwargs=kwargs, output_json=output_json,
        )
    click.echo(f"Finished. Check {output_log} and {output_json} for details.")


def print_conflicts_info(conflicts):
    click.echo("There are following conflicts waiting to be resolved:")
    for _id, conflict in conflicts.items():
        click.echo("")
        click.echo(f"{conflict.id}:")
        conflict_name = conflict.id
        for line in conflict.summary:
            click.echo(f"\t{line}")
    click.echo("")
    click.echo("Please run 'journey.py resolve <Conflict>' to apply sample fixes.")
    click.echo(f"Example 'journey.py resolve {conflict_name}'")
    click.echo("")
    click.echo(
        "Alternatively to resolve all the conflicts automatically, run 'journey.py resolve-all'"
    )


def print_no_conflict_info(history):
    click.echo("No conflicts has been found.")
    click.echo("")
    click.echo("In order to generate output ucs, run 'journey.py generate'")

    if not history:
        return

    click.echo("")
    click.echo(
        "In order to review the changes history, run 'journey.py history' or 'journey.py history --details'"
    )


def print_conflict_resolution_help(
    conflict_info, working_directory, config_path, mitigation_branches
):
    click.echo(f"Workdir: {working_directory}")
    click.echo(f"Config path: {config_path}\n")
    click.echo(f"Resolving conflict_info {conflict_info.id}\n")
    click.echo(
        f"Resolve the issues on objects commented with '{conflict_info.id}' in the following files:"
    )
    for filename in conflict_info.files_to_render:
        click.echo(f"\t{filename}")

    click.echo("")
    click.echo("Proposed mitigations are listed below:")
    for mitigation_branch in mitigation_branches:
        click.echo(f"\t{mitigation_branch}")
    click.echo("")
    click.echo("To view the mitigation content, run 'journey.py show <mitigation>'")
    click.echo(f"Example 'journey.py show {mitigation_branch}'")
    click.echo("")
    click.echo("To view the issues found, run 'journey.py diff'")
    click.echo("")
    click.echo(
        "To apply proposed changes right away, run " "'journey.py use <mitigation>'"
    )
    click.echo(f"Example 'journey.py use {mitigation_branch}'")
    click.echo("")

    click.echo(
        "Alternatively, the files can be edited manually followed by running 'journey.py migrate' command."
    )


def print_destination_system_prerequisites():
    click.echo(
        "Before deploying to Destination System, following requirements should be met:"
    )
    click.echo("\tHandling the master key.")
    click.echo("\t\tRun 'f5mku -K' on the Source System and copy the output")
    click.echo("\t\tRun 'f5mku -r <copied value> on the Destination System")
    click.echo("")

    click.echo("\tVelos VM tenat should be deployed.")
    click.echo(
        "\tVLANs, trunks and interfaces should be configured on the Controller and assigned to the Tenant."
    )
    click.echo(
        "\tAll modules from the Source System should be provisioned "
        "(except PEM and CGNAT which are not supported yet)"
    )


@contextmanager
def error_handler():
    try:
        yield
    except AlreadyInitializedError as e:
        click.echo("Migration process has already been started.")
        click.echo(
            f"In order to start processing new ucs file run 'journey.py start {e.input} --clear'"
        )

    except ArchiveOpenError:
        click.echo("Failed to open the archive.")
        click.echo("")
        click.echo(
            "If the archive is encrypted, rerun with --ucs-passphrase <passphrase> parameter."
        )

    except ArchiveDecryptError:
        click.echo("Failed to decrypt the archive.")
        click.echo("")
        click.echo("Make sure that appropriate passphrase was passed.")

    except NotMasterBranchError:
        click.echo("Please checkout to master branch.")

    except NotInitializedError:
        click.echo("The migration process has not been started yet.")
        click.echo(
            "In order to start new Migration process, run 'journey.py start <ucs>'"
        )
        click.echo("")
        click.echo(
            "To download the ucs from a source system, use 'journey download-ucs' command."
        )
        click.echo("Run 'journey download-ucs --help' for more details.")

    except ConflictNotResolvedError as e:
        click.echo(f"Current conflict_info {e.conflict_id} is not yet resolved.")
        click.echo("")
        print_conflict_resolution_help(
            conflict_info=e.conflict_info,
            working_directory=e.working_directory,
            config_path=e.config_path,
            mitigation_branches=e.mitigation_branches,
        )

    except DifferentConflictError as e:
        click.echo(
            f"Conflict {e.conflict_id} resolution already in progress."
            "Finish it by calling 'journey.py migrate' first before starting a new one."
        )
    except UnknownConflictError as e:
        click.echo(
            f"Invalid conflict_info ID ({e.conflict_id}) - given conflict_info not found in the config."
        )
    except NotAllConflictResolvedError:
        click.echo("There still are some unresolved conflicts.")
        click.echo("")
        click.echo("In order to handle them, run 'journey.py migrate'")
        click.echo("Or rerun the command with '--force' flag")
    except OutputAlreadyExistsError as e:
        click.echo(f"File '{e.output}' already exists.")
        click.echo(
            "In order to overwrite the file, rerun the command with '--overwrite' flag"
        )
    except LocalChangesDetectedError as e:
        click.echo("Local changes detected in following files:")
        for path in e.uncommitted:
            click.echo(f"\t{path}")
        click.echo('Run \'journey.py migrate --message "<message>" to apply changes.')
        click.echo("Run 'journey.py cleanup' to discard changes.")
    except AS3InputDoesNotExistError:
        click.echo("The specified AS3 file does not exist.")

    except DeviceAuthenticationError as e:
        click.echo("Cannot authenticate to BIGIP check given credentials. ")
        click.echo(f"HOST: {e.host}")
        click.echo(f"USER: {e.ssh_username}")
    except NetworkConnectionError:
        click.echo(
            "There are some problems with you network connection please check it."
        )


def process_and_print_output(controller: MigrationController, commit_name: str = None):
    current_conflicts = controller.process(commit_name=commit_name)
    if current_conflicts:
        print_conflicts_info(conflicts=current_conflicts)
    else:
        print_no_conflict_info(history=controller.history)


if __name__ == "__main__":
    try:
        cli()  # pylint: disable=E1120
    except Exception as e:
        log.exception(e, exc_info=True)
        raise
