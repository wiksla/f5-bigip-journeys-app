import os

from journeys.validators.deployment import get_mcp_status
from journeys.validators.deployment import get_tmm_global_status
from journeys.validators.deployment import load_ucs


def test_load_ucs(bigip_mock):
    test_path = "/tmp/test.ucs"
    load_ucs(bigip_mock, test_path)
    bigip_mock.icontrol.mgmt.shared.file_transfer.ucs_uploads.upload_file.assert_called_with(
        test_path
    )
    bigip_mock.icontrol.mgmt.tm.sys.ucs.exec_cmd.assert_called_with(
        command="load",
        name=os.path.basename(test_path),
        options=[{"no-license": True, "platform-migrate": True}],
    )


def test_get_mcp_status(bigip_mock):
    status = get_mcp_status(bigip_mock)
    assert status["last-load"] == "full-config-load-succeed"
    assert status["phase"] == "running"
    assert status["end-platform-id-received"] == "true"


def test_get_tmm_global_status(bigip_mock):
    status = get_tmm_global_status(bigip_mock)
    assert status["memory-total"] == "6.1G"
    assert status["npus"] == "2"
