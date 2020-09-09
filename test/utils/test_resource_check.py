import pytest
from fabric import Result
from mock import create_autospec

from journeys.utils.device import Device
from journeys.utils.device import SSHConnector
from journeys.utils.resource_check import _parse_stderr
from journeys.utils.resource_check import build_mprov_cfg
from journeys.utils.resource_check import check_mprov_cfg

STDERR_NO_VALUE_FOUND = "'No value found for DB variable (provision.datastor).'"

STDOUT_PROPER = """'Fetching TMM count.'
'Bad number of TMMs (0) - setting to 2'
'Number of TMMs = 2'
'Fetching TMM thread count.'
'Number of TMM threads = 2'
'Processing lvm test'
'lvm test complete'
'getDiskMiB_Available: 25832'
'getDiskMiB_Potential: 25832'
'Skipping disk minimum check - Provisioned without disk-based modules'
'There are NO extra disks.'
'Maximum hit for tmos mem'
'Provisioning (validation) successful.'
provisioned.memory.ui=130

provisioned.memory.host=1836
provisioned.cpu.host=10
provisioned.disk.host=25832
"""

STDERR_NO_RESOURCES = """'No value found for DB variable (provision.datastor).'
'No value found for DB variable (provision.platform).'
'Fetching TMM count.'
'Bad number of TMMs (0) - setting to 2'
'Number of TMMs = 2'
'Fetching TMM thread count.'
'Number of TMM threads = 2'
'Processing lvm test'
'lvm test complete'
'getDiskMiB_Available: 45920'
'getDiskMiB_Potential: 45920'
'There are NO extra disks.'
'Disk limit exceeded. 48238 MB are required to provision these modules, but only 45920 MB are available.'
'Provisioning (validation) failed.'
"""

MPROV_CFG_FILE = """provision.platform=Z101
provision.level.ltm=nominal
provision.level.apm=minimal
provision.extramb=0"""


# TODO: need additional adjustment with validators Unit-tests.


def test_build_mprov_cfg(tmpdir):
    file = tmpdir.join("mprov.cfg")
    build_mprov_cfg(
        mprov_path=file,
        platform="Z101",
        provisioned_modules={"ltm": "nominal", "apm": "minimal"},
        extramb="0",
    )
    assert file.read() == MPROV_CFG_FILE


def test_minimum_recommended_resources_are_met(device_mock, result_mock):
    result_mock.stdout = STDOUT_PROPER
    device_mock.ssh.run.return_value = result_mock
    assert (
        check_mprov_cfg(device_mock, mprov_cfg_location="")
        == "Minimum recommended requirements for resources are met."
    )


def test_lack_of_resources(device_mock, result_mock):
    result_mock.stderr = STDERR_NO_RESOURCES
    device_mock.ssh.run.return_value = result_mock
    assert (
        check_mprov_cfg(device_mock, mprov_cfg_location="")
        == "Minimum recommended requirements for resources are not met.\n"
        "Disk limit exceeded. 48238 MB are required to provision these modules, but only 45920 MB are available."
    )


def test_stderr_no_value_not_trigger_message(result_mock):
    result_mock.stderr = STDERR_NO_VALUE_FOUND
    assert _parse_stderr(result_mock) == ""


@pytest.yield_fixture()
def result_mock(stdout="", stderr="", exited=0, **kwargs):
    """obj of fabric.Results with values."""
    result_mock = create_autospec(Result)
    kwargs.update({"stdout": stdout, "stderr": stderr, "exited": exited})
    result_mock.configure_mock(**kwargs)
    return result_mock


@pytest.yield_fixture()
def ssh_connector_mock():
    mock_ssh_connector = create_autospec(SSHConnector)
    mock_config = {
        "host": "10.0.0.10",
        "run.return_value": None,
    }
    mock_ssh_connector.configure_mock(**mock_config)
    yield mock_ssh_connector


@pytest.yield_fixture()
def device_mock(ssh_connector_mock):
    mock_device = create_autospec(Device)
    mock_config = {
        "host": "10.0.0.10",
        "ssh": ssh_connector_mock,
    }
    mock_device.configure_mock(**mock_config)
    yield mock_device
