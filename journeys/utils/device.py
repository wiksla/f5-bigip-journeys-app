import os

from f5.bigip import ManagementRoot
from fabric import Connection
from paramiko.sftp_attr import SFTPAttributes

from journeys.utils.image import Version
from journeys.utils.image import parse_version_file


class SSHConnector:
    def __init__(self, host, root_username, root_password):
        self.host = host
        self.ssh_username = root_username
        self.ssh_password = root_password

    @property
    def fabric(self):
        return {
            "user": self.ssh_username,
            "connect_kwargs": {"password": self.ssh_password},
        }

    def run(self, cmd: str, raise_error=True):
        with Connection(host=self.host, **self.fabric) as c:
            result = c.run(cmd, hide=True, warn=not raise_error)
        return result

    def run_transaction(self, cmds):
        """ ['disk', 'tmsh show /sys hardware field-fmt', _disk_validate ] """
        results = {}
        with Connection(host=self.host, **self.fabric) as c:
            for name, cmd, validator in cmds:
                result = c.run(cmd, hide=True)
                results[name] = validator(result)
        return results


class APIConnector:
    def __init__(self, host, api_username, api_password):
        self.mgmt = self.mgmt = ManagementRoot(host, api_username, api_password)


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
    with Connection(device.ssh.host, **device.ssh.fabric) as c:
        return c.sftp().stat(remote)


def get_file(device: Device, remote: str, local: str) -> str:
    with Connection(device.ssh.host, **device.ssh.fabric) as c:
        return c.get(remote, local)


def get_ucs(device: Device, remote: str, local_ucs_name: str):
    with Connection(device.ssh.host, **device.ssh.fabric) as c:
        return c.get(remote, local_ucs_name)


def list_dir(device: Device, directory: str):
    with Connection(device.ssh.host, **device.ssh.fabric) as c:
        return c.sftp().listdir(directory)


def save_ucs(device: Device, ucs_name: str, ucs_passphrase: str):
    ucs_remote_dirname = "/var/local/ucs/"
    cmd = f"tmsh save sys ucs {ucs_name}"
    if ucs_passphrase:
        cmd += f" passphrase {ucs_passphrase}"
    device.ssh.run(cmd=cmd)
    if not ucs_name.endswith(".ucs"):
        ucs_name += ".ucs"
    return os.path.join(ucs_remote_dirname, ucs_name)


def get_image(device: Device) -> Version:
    result = device.ssh.run(cmd="cat /VERSION")
    return Version(**(parse_version_file(result.stdout)))


def obtain_source_resources(device: Device) -> dict:
    return device.ssh.run_transaction(
        cmds=[
            ("disk", "tmsh show /sys hardware field-fmt", _obtain_disk_size),
            ("ram", "tmsh show /sys memory field-fmt", _obtain_memory),
            ("cores", "tmsh show /sys hardware field-fmt", _obtain_cpu_cores_no),
        ],
    )


def delete_ucs(device: Device, ucs_location: str):
    device.ssh.run(f"rm -rf {ucs_location}")


def _obtain_disk_size(result):
    result = result.stdout.splitlines()
    for idx, line in enumerate(result):
        if "versions.2.name Size" == line.lstrip():
            return result[idx + 1].lstrip().split()[-1]


def _obtain_cpu_cores_no(result):
    result = result.stdout.splitlines()
    for idx, line in enumerate(result):
        if "versions.1.name cores" == line.lstrip():
            return result[idx + 1].lstrip().split()[1]


def _obtain_memory(result):
    for line in result.stdout.splitlines():
        line = line.lstrip()
        if line.startswith("memory-total"):
            return line.split()[-1]
