import os

from fabric import Connection

from journeys.utils.image import Version
from journeys.utils.image import parse_version_file


class Device:
    """ Class representing DUT credentials. """

    def __init__(self, ip: str, username: str, password: str):
        self.ip = ip
        self.username = username
        self.password = password

    @property
    def fabric(self):
        return {"user": self.username, "connect_kwargs": {"password": self.password}}

    def run_ssh_cmd(self, cmd: str):
        with Connection(host=self.ip, **self.fabric) as c:
            result = c.run(cmd, hide=True)
        return result

    def run_ssh_cmd_transaction(self, cmds: list) -> dict:
        """ ['disk', 'tmsh show /sys hardware field-fmt', _disk_validate ] """
        results = {}
        with Connection(host=self.ip, **self.fabric) as c:
            for name, cmd, validator in cmds:
                result = c.run(cmd, hide=True)
                results[name] = validator(result)
        return results

    def obtain_source_resources(self) -> dict:
        return self.run_ssh_cmd_transaction(
            cmds=[
                ("disk", "tmsh show /sys hardware field-fmt", _obtain_disk_size),
                ("ram", "tmsh show /sys memory field-fmt", _obtain_memory),
                ("cores", "tmsh show /sys hardware field-fmt", _obtain_cpu_cores_no),
            ],
        )

    def get_image(self) -> Version:
        result = self.run_ssh_cmd(cmd="cat /VERSION")
        return Version(**(parse_version_file(result.stdout)))

    def get_ucs(self, remote: str, local_ucs_name: str):
        with Connection(self.ip, **self.fabric) as c:
            result = c.get(remote, local_ucs_name)
        return result

    def save_ucs(self, ucs_name: str):
        ucs_remote_dirname = "/var/local/ucs/"
        self.run_ssh_cmd(f"tmsh save sys ucs {ucs_name}")
        return os.path.join(ucs_remote_dirname, ucs_name)

    def delete_ucs(self, ucs_location):
        self.run_ssh_cmd(f"rm -rf {ucs_location}")


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
