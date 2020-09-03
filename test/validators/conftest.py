import os
import shutil
from pathlib import Path
from typing import Set

import pytest
from fabric import Connection
from fabric import Result
from fabric.transfer import Result as TransferResult
from mock import MagicMock
from mock import create_autospec
from paramiko import SFTPAttributes

from journeys.utils.device import Device
from journeys.utils.device import SSHConnector
from journeys.validators.exceptions import TestConfigurationError

TEST_DATA_ROOT = (
    Path(__file__).parent.parent.parent.resolve() / "test" / "validators" / "test_data"
)
TEST_OUTPUT_ROOT = (
    Path(__file__).parent.parent.parent.resolve() / "test" / "validators" "test_output"
)

mocked_device_a = "bigip"
mocked_device_b = "velos"

"""In some cases you may want to run test suite against real Big-IP.
Fill variables below and make use of `bigip` fixture"""

BIGIP_IP_ADDRESS = os.environ.get("BIGIP_IP_ADDRESS")
BIGIP_ADMIN_USER = os.environ.get("BIGIP_IP_ADMIN_USER", "admin")
BIGIP_ADMIN_PASSWORD = os.environ.get("BIGIP_ADMIN_PASSWORD", "admin")
BIGIP_ROOT_PASSWORD = os.environ.get("BIGIP_ROOT_PASSWORD", "default")

"""Below is set of tmsh commands that are mocked inside DUTs
If you want to use new mocked tmsh command, please make sure you add
commands test output in corresponding folder inside TEST_DATA_ROOT"""

commands_set = {
    "tmsh show sys mcp-state field-fmt",
    "tmsh show sys tmm-info field-fmt global",
    "tmsh list sys db all-properties one-line",
    "tmsh show sys software status",
    "tmsh show sys mcp-state field-fmt",
    "tmsh show sys tmm-info field-fmt global",
    "python /usr/libexec/sys-eicheck.py",
    "tmm --clientciphers 'DEFAULT'",
    "ls -1 /etc/cron.daily",
    "ls -1 /etc/cron.weekly",
    "cat /etc/crontab",
    "cut -d: -f1 /etc/passwd",
    "crontab -l -u admin",
}

if not Path(TEST_OUTPUT_ROOT).exists():
    Path(TEST_OUTPUT_ROOT).mkdir()


class DeviceTestData:
    """Class supplying Test Data to mocked Device object."""

    def __init__(self, dv: str, commands: set, test_data_root=TEST_DATA_ROOT):
        self.test_data_root = test_data_root
        self.device_name = dv
        self.commands = commands

    @property
    def commands(self):
        """Return mapping of command <-> Mock obj of fabric.Result with values."""
        return self.__commands

    @commands.setter
    def commands(self, commands_set: set):
        cmd_value_dict = {}
        for cmd in commands_set:
            try:
                result_mock = self.load_mocked_values_for_run_cmd(cmd)
                cmd_value_dict[cmd] = result_mock
            except IsADirectoryError as err:
                raise TestConfigurationError(
                    f"Command is an empty string? File path "
                    f"points to directory: {err}"
                )
            except FileNotFoundError as err:
                print(f"WARNING! Can't find data for command: '{cmd}'\n{err}")
        self.__commands = cmd_value_dict

    def load_mocked_values_for_run_cmd(self, cmd):
        """Load return values for run method from file with corresponding filename."""
        filename = (
            cmd.replace(" ", "_")
            .replace("-", "_")
            .replace(".py", "")
            .replace("/", ".")
            .replace(":", ".")
        )
        stdout = (self.path / filename).read_text()
        stderr_path = self.path / f"{filename}_stderr"
        exited_path = self.path / f"{filename}_exited"
        stderr = stderr_path.read_text() if stderr_path.exists() else ""
        exited = int(exited_path.read_text()) if exited_path.exists() else 0
        return self.result_mock(stdout, stderr, exited)

    @property
    def device_name(self) -> str:
        """Return device name."""
        return self.__device_name

    @property
    def path(self) -> Path:
        """Path to device directory in test_data."""
        return Path(f"{self.test_data_root}/{self.device_name}/")

    @device_name.setter
    def device_name(self, device_name: str):
        if Path(f"{self.test_data_root}/{device_name}").exists():
            self.__device_name = device_name
        else:
            raise TestConfigurationError(
                f"Directory {device_name} not found! \n"
                f" Path: {self.test_data_root}/{device_name}"
            )

    @classmethod
    def result_mock(cls, stdout="", stderr="", exited=0, **kwargs):
        """Return Mock obj of fabric.Results with values."""
        result_mock = create_autospec(Result)
        kwargs.update({"stdout": stdout, "stderr": stderr, "exited": exited})
        result_mock.configure_mock(**kwargs)
        return result_mock

    @classmethod
    def get_test_output(cls, commands_set: Set, device_name: str):
        """Return facade function that replaces run.side_effect."""
        test_data = cls(
            dv=device_name, commands=commands_set, test_data_root=TEST_DATA_ROOT
        )

        def commands(*args, **kwargs):
            return (
                test_data.commands[kwargs["cmd"]]
                if "cmd" in kwargs
                else test_data.commands.get(args[0], cls.result_mock())
            )

        return commands


@pytest.yield_fixture(scope="session")
def get_file_output():
    """Return facade function that returns list_dir.side_effect."""
    fs_root = TEST_DATA_ROOT / "bigip" / "filesystem_root"
    output = TEST_OUTPUT_ROOT / "local_temp_fs"
    if not output.exists():
        output.mkdir()

    def getfile(filepath: str, destination_path: str) -> TransferResult:
        if filepath.startswith("/"):
            filepath = filepath[1:]
        origin_local = fs_root / filepath
        if not origin_local.exists():
            raise TestConfigurationError(
                f"File: {filepath} not found in: {fs_root})\n"
                "Make sure to prepare files to mock on bigip before running your "
                "test! "
            )
        shutil.copyfile(origin_local, destination_path)

        return TransferResult(
            destination_path,
            str(origin_local),
            str(origin_local),
            str(origin_local),
            create_autospec(Connection),
        )

    return getfile


@pytest.yield_fixture(scope="session")
def stat_file_output():
    """Return facade function that returns list_dir.side_effect."""
    fs_root = TEST_DATA_ROOT / "bigip" / "filesystem_root"

    def statfile(filepath: str) -> SFTPAttributes:
        if filepath.startswith("/"):
            filepath = filepath[1:]
        try:
            stat_result = os.stat(fs_root / filepath)
        except FileNotFoundError:
            raise TestConfigurationError(
                f"File: {filepath} not found in: {fs_root})\n"
                "Make sure to prepare files to mock on bigip before running your "
                "test! "
            )
        stat_mock = create_autospec(SFTPAttributes)
        st_set = {"st_size", "st_uid", "st_gid", "st_mode", "st_atime", "st_mtime"}
        mock_config = {st: stat_result.__getattribute__(st) for st in st_set}
        stat_mock.configure_mock(**mock_config)
        return stat_mock

    return statfile


@pytest.yield_fixture(scope="session")
def ssh_connector_mock():
    """ Mock for ssh connector """
    mock_ssh_connector = create_autospec(SSHConnector)
    commands = DeviceTestData.get_test_output(commands_set, mocked_device_a)
    mock_config = {
        "host": "10.0.0.10",
        "run.side_effect": commands,
    }
    mock_ssh_connector.configure_mock(**mock_config)
    yield mock_ssh_connector


@pytest.yield_fixture(scope="session")
def bigip_mock(ssh_connector_mock):
    """Mock for bigip operations."""
    mock_bigip = create_autospec(Device)
    mock_config = {
        "host": "10.0.0.10",
        "ssh": ssh_connector_mock,
        "icontrol": MagicMock(),
    }
    mock_bigip.configure_mock(**mock_config)
    yield mock_bigip


@pytest.yield_fixture(scope="session")
def velos_mock(ssh_connector_mock):
    """Mock for velos operations."""
    mock_bigip = create_autospec(Device)
    mock_config = {
        "host": "10.0.0.10",
        "ssh": ssh_connector_mock,
        "icontrol": MagicMock(),
    }
    mock_bigip.configure_mock(**mock_config)
    yield mock_bigip
