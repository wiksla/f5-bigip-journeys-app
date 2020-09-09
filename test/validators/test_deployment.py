from journeys.validators.deployment import get_mcp_status
from journeys.validators.deployment import get_tmm_global_status


def test_get_mcp_status(bigip_mock):
    status = get_mcp_status(bigip_mock)
    assert status["last-load"] == "full-config-load-succeed"
    assert status["phase"] == "running"
    assert status["end-platform-id-received"] == "true"


def test_get_tmm_global_status(bigip_mock):
    status = get_tmm_global_status(bigip_mock)
    assert status["memory-total"] == "6.1G"
    assert status["npus"] == "2"
