import json
from pathlib import Path
from test.validators.conftest import TEST_DATA_ROOT
from unittest.mock import MagicMock
from unittest.mock import patch

from deepdiff import DeepDiff

from journeys.validators.db_comparer import compare_db
from journeys.validators.db_comparer import get_dbs_from_devices

stub = json.loads(
    Path(f"{TEST_DATA_ROOT}/bigip/mgmt.tm.sys.dbs.get_collection").read_text()
)


@patch(
    "journeys.validators.db_comparer.get_all_dbs_raw", MagicMock(return_value=stub),
)
def test_get_dbs_from_devices(bigip_mock, velos_mock):
    dbs = get_dbs_from_devices(bigip_mock, velos_mock)
    assert type(dbs) == list
    assert len(dbs) == 2
    bigip_db, velos_db = dbs[0], dbs[1]
    assert bigip_db == velos_db


@patch(
    "journeys.validators.db_comparer.get_dbs_from_devices",
    MagicMock(return_value=[stub, stub]),
)
def test_compare_db(bigip_mock, velos_mock):
    db_diff = compare_db(bigip_mock, velos_mock)
    assert type(db_diff) == DeepDiff
    assert not db_diff
