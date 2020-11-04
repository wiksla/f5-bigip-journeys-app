import inspect
import logging
import os
import socket
from contextlib import contextmanager
from typing import Callable
from typing import Optional
from typing import Union

import paramiko
from f5.bigip import ManagementRoot
from fabric import Connection
from icontrol.exceptions import iControlUnexpectedHTTPError
from invoke import Failure
from invoke import ThreadException
from invoke import UnexpectedExit
from paramiko.sftp_attr import SFTPAttributes

from journeys.errors import DeviceAuthenticationError
from journeys.errors import SSHConnectionError
from journeys.errors import UcsActionError
from journeys.utils.image import Version
from journeys.utils.image import parse_version_file

REMOTE_UCS_DIRECTORY = "/var/local/ucs/"

log = logging.getLogger(__name__)


def format_ucs_load_command(ucs: str, ucs_passphrase: str):
    cmd = f"tmsh load sys ucs {ucs} platform-migrate no-license keep-current-management-ip"
    if ucs_passphrase:
        cmd += f" passphrase {ucs_passphrase}"
    return cmd


def format_ucs_save_command(ucs: str, ucs_passphrase: str):
    cmd = f"tmsh save sys ucs {ucs}"
    if ucs_passphrase:
        cmd += f" passphrase {ucs_passphrase}"

    return cmd


class SSHConnector:
    def __init__(self, host, root_username, root_password):
        self.host = host
        self.ssh_username = root_username
        self.ssh_password = root_password

    @property
    def fabric(self):
        return {
            "user": self.ssh_username,
            "connect_kwargs": {"password": self.ssh_password, "timeout": 30},
        }

    @contextmanager
    def connection(self, extra_kwargs: dict = None):
        kwargs = self.fabric
        if extra_kwargs:
            kwargs.update(extra_kwargs)
        with Connector(host=self.host, **kwargs) as c:
            yield c

    def run(self, cmd: str, raise_error=True):
        with self.connection() as c:
            result = c.run(cmd, hide=True, warn=not raise_error)
        return result

    def run_transaction(self, cmds):
        """ ['disk', 'tmsh show /sys hardware field-fmt', _disk_validate ] """
        results = {}
        with self.connection() as c:
            for name, cmd, validator in cmds:
                result = c.run(cmd, hide=True)
                results[name] = validator(result)
        return results


def _connector_func_decorator(func_, retry):
    def decorator(*args, **kwargs):
        errors = []
        for i in range(retry):
            try:
                return func_(*args, **kwargs)
            except paramiko.AuthenticationException:
                raise DeviceAuthenticationError(
                    host=args[0].host, ssh_username=args[0].user
                )
            except FileNotFoundError:
                raise
            except PermissionError:
                raise
            except (paramiko.SSHException, socket.error, ConnectionResetError,) as e:
                errors.append(e)
                log.debug(f"Connection error: {e}. Retrying.. [{i}/{retry}].")
                continue
        else:
            raise SSHConnectionError(
                f"SSH connection retry unsuccessful. Latest error: {errors[-1]}"
            )

    return decorator


def error_handler(funcs_, retry):
    def wrapped(cls):
        for name, method in inspect.getmembers(cls):
            if name in funcs_:
                setattr(cls, name, _connector_func_decorator(func_=method, retry=retry))
        return cls

    return wrapped


@error_handler(["get", "run", "put", "sftp"], retry=3)
class Connector(Connection):
    pass


class APIConnector:
    def __init__(self, host, api_username, api_password):
        try:
            self.mgmt = ManagementRoot(host, api_username, api_password)
        except iControlUnexpectedHTTPError as e:
            log.error(e)
            if e.response.status_code == 401:
                raise DeviceAuthenticationError(host, api_username)
            e.response.raise_for_status()


class Device:
    def __init__(
        self,
        host: str,
        ssh_username: str,
        ssh_password: str,
        api_username: str = None,
        api_password: str = None,
    ):

        self.host = host
        self.ssh = SSHConnector(
            host=host, root_username=ssh_username, root_password=ssh_password
        )

        if api_username and api_password:
            self.icontrol = APIConnector(
                host=host, api_username=api_username, api_password=api_password
            )


def stat_file(device: Device, remote: str) -> SFTPAttributes:
    with device.ssh.connection() as c:
        return c.sftp().stat(remote)


def get_file(
    device: Device, remote: str, local: str, callback: Optional[Callable] = None
) -> None:
    with device.ssh.connection() as c:
        c.sftp().get(remote, local, callback=callback)


def put_file(
    device: Device,
    local: Union[str, bytes],
    remote: str,
    callback: Optional[Callable] = None,
) -> None:
    with device.ssh.connection() as c:
        c.sftp().put(local, remote, callback=callback)


def list_dir(device: Device, directory: str):
    with device.ssh.connection() as c:
        return c.sftp().listdir(directory)


def save_ucs(device: Device, ucs_name: str, ucs_passphrase: str) -> str:
    cmd = format_ucs_save_command(ucs=ucs_name, ucs_passphrase=ucs_passphrase)
    try:
        device.ssh.run(cmd=cmd)
    except (UnexpectedExit, Failure, ThreadException) as err:
        log.error(err)
        raise UcsActionError(action_name="Saving Ucs")

    if not ucs_name.endswith(".ucs"):
        ucs_name += ".ucs"
    return os.path.join(REMOTE_UCS_DIRECTORY, ucs_name)


def load_ucs(device: Device, ucs: str, ucs_passphrase: str) -> None:
    ucs = os.path.basename(ucs)
    cmd = format_ucs_load_command(ucs=ucs, ucs_passphrase=ucs_passphrase)
    try:
        device.ssh.run(cmd=cmd)
    except (UnexpectedExit, Failure, ThreadException) as err:
        log.error(err)
        raise UcsActionError(action_name="Loading Ucs")


def get_image(device: Device) -> Version:
    result = device.ssh.run(cmd="cat /VERSION")
    return Version(**(parse_version_file(result.stdout)))


def delete_file(device: Device, remote: str):
    device.ssh.run(f"rm -rf {remote}")
