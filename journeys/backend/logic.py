import datetime
import os
import random
import string
from contextlib import suppress

from journeys.backend import models

from ..controller import MigrationController
from ..utils import device as device_module
from ..validators import exceptions

_controller = None


def get_controller(
    session: models.Session, clear: bool = False, allow_empty: bool = False
) -> MigrationController:
    global _controller

    if not _controller:

        with suppress(FileExistsError):
            os.mkdir(session.working_directory)

        _controller = MigrationController(
            working_directory=session.working_directory,
            clear=clear,
            allow_empty=allow_empty,
        )
    return _controller


def download_ucs(
    session: models.Session,
    system_credentials: models.SystemCredentials,
    check_version=False,
    delete_file=True,
):
    now = datetime.datetime.now()
    output = f"journey-{now.strftime('%Y%m%d-%H%M%S')}.ucs"
    ucs_passphrase = "".join(
        random.choice(string.ascii_letters + string.digits) for i in range(10)
    )

    device = device_module.Device(
        host=system_credentials.host,
        ssh_username=system_credentials.username,
        ssh_password=system_credentials.password,
    )

    if check_version:
        version = device_module.get_image(device=device)
        if not version.is_velos_supported():
            raise exceptions.JourneysError(
                f"Target system version {version} is not supported by VELOS"
            )

    ucs_remote_dir = device_module.save_ucs(
        device=device, ucs_name=output, ucs_passphrase=ucs_passphrase
    )

    local_ucs_path = device_module.get_file(
        device=device,
        remote=ucs_remote_dir,
        local=os.path.join(session.working_directory, output),
    )

    if delete_file:
        device_module.delete_file(device=device, remote=ucs_remote_dir)

    return local_ucs_path.local, ucs_passphrase


def initialize(
    session: models.Session,
    ucs_file,
    ucs_passphrase,
    as3_file,
    clear=False,
    credentials=None,
):
    controller = get_controller(session=session, clear=clear, allow_empty=True)
    controller.initialize(
        input_ucs=os.path.join(session.working_directory, ucs_file),
        ucs_passphrase=ucs_passphrase,
        as3_path=os.path.join(session.working_directory, as3_file)
        if as3_file
        else None,
    )
    source = models.Source(
        has_ucs=True, has_as3=True if as3_file else False, credentials=credentials
    )
    source.save()
    session.source = source
    session.save()
    process(session=session, first_run=True)


def process(session: models.Session, commit_name=None, first_run: bool = False):
    controller = get_controller(session=session)
    # clear previous conflicts
    commit_before_process = controller.repo.head.commit.hexsha
    conflicts = controller.process(commit_name=commit_name)
    commit = controller.repo.head.commit.hexsha
    if not first_run:
        if commit == commit_before_process:
            return

        models.Change(
            session=session,
            commit=commit,
            message=controller.repo.head.commit.message,
            content=controller.repo.git.show(commit),
        ).save()

    if session.current_conflict:
        # At this point the conflict is resolved, because if it would not be then controller.process would raise a
        # Conflict not resolved exception
        session.current_conflict = None
        session.save()

    models.File.objects.filter(session=session).delete()  # pylint: disable=E1101
    models.Mitigation.objects.filter(session=session).delete()  # pylint: disable=E1101
    models.Conflict.objects.filter(session=session).delete()  # pylint: disable=E1101
    for conflict in conflicts.values():
        models.Conflict(
            name=conflict.id, summary="\n".join(conflict.summary), session=session
        ).save()


def set_current_conflict(session: models.Session, conflict_id):
    controller = get_controller(session=session)
    conflict_info, _, config_path, mitigation_branches = controller.resolve(
        conflict_id=conflict_id
    )
    session.current_conflict = conflict_id
    conflict = models.Conflict.objects.get(  # pylint: disable=E1101
        name=conflict_id, session=session
    )
    session.save()

    models.File.objects.filter(session=session).delete()  # pylint: disable=E1101
    models.Mitigation.objects.filter(session=session).delete()  # pylint: disable=E1101

    # TODO: files_to_render should contain "config" prefix
    file_paths = [
        os.path.join("config", file_to_render)
        for file_to_render in conflict_info.files_to_render
    ]

    for file_path in file_paths:
        models.File(path=file_path, session=session, conflict=conflict).save()

    for mitigation_branch in mitigation_branches:
        mitigation = models.Mitigation(
            name=mitigation_branch.name, session=session, conflict=conflict
        )
        mitigation.save()
        for file_path in file_paths:
            models.File(
                path=file_path,
                session=session,
                conflict=conflict,
                mitigation=mitigation,
            ).save()


def reset_current_conflict(session: models.Session):
    controller = get_controller(session=session)
    controller.abort()
    session.current_conflict = None
    session.save()
    models.File.objects.filter(session=session).delete()  # pylint: disable=E1101
    models.Mitigation.objects.filter(session=session).delete()  # pylint: disable=E1101
