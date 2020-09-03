from json import loads
from pathlib import Path
from test.validators.conftest import TEST_DATA_ROOT

from journeys.validators.ltm_checks import get_ltm_vs_status


def test_get_ltm_vs_status(bigip_mock):
    class Collection:
        def __init__(self, name):
            self.name = name
            self.stats = self

        def load(self):
            return self

        def to_dict(self):
            return loads(
                Path(
                    f"{TEST_DATA_ROOT}/bigip/mgmt_tm_ltm_virtual_vs-name_stats"
                ).read_text()
            )

    bigip_mock.icontrol.mgmt.tm.ltm.virtuals.get_collection = lambda: [
        Collection("vs_1"),
        Collection("vs_2"),
    ]

    status = get_ltm_vs_status(bigip_mock)
    assert status["vs_1"]["status.availabilityState"] == {"description": "unknown"}
    assert status["vs_1"]["status.enabledState"] == {"description": "enabled"}
    assert status["vs_1"]["status.statusReason"] == {
        "description": "The children pool member(s) either "
        "don\\'t have service checking "
        "enabled, or service check results are "
        "not available yet"
    }

    assert status["vs_2"]["status.availabilityState"] == {"description": "unknown"}
    assert status["vs_2"]["status.enabledState"] == {"description": "enabled"}
    assert status["vs_2"]["status.statusReason"] == {
        "description": "The children pool member(s) either "
        "don\\'t have service checking "
        "enabled, or service check results are "
        "not available yet"
    }
