import json
import logging
from pathlib import Path
from test.validators.conftest import TEST_DATA_ROOT
from test.validators.conftest import TEST_OUTPUT_ROOT
from unittest.mock import MagicMock
from unittest.mock import patch

from deepdiff import DeepDiff

from journeys.validators.comparers import compare_ciphersuites
from journeys.validators.comparers import compare_db
from journeys.validators.comparers import compare_memory_footprint
from journeys.validators.comparers import get_dbs_from_devices
from journeys.validators.comparers import get_modules_footprint_from_devices
from journeys.validators.comparers import tmsh_compare
from journeys.validators.comparers import tmsh_compare_as_html


def test_compare_db_as_html(bigip_mock, velos_mock, caplog):
    cmd = "tmsh list sys db all-properties one-line"
    html_diff = tmsh_compare_as_html(cmd, bigip_mock, velos_mock, wrapcolumn=160)
    if caplog.handler.level == logging.DEBUG:
        Path(f"{TEST_OUTPUT_ROOT}/test_compare_db_as_html.html").write_text(html_diff)
    assert type(html_diff) == str


def test_compare_tmsh_show_sys_soft(bigip_mock, velos_mock):
    cmd = "tmsh show sys software status"
    aaa = tmsh_compare(cmd, bigip_mock, velos_mock)
    assert type(aaa) == str


stub = json.loads(
    Path(f"{TEST_DATA_ROOT}/bigip/mgmt.tm.sys.dbs.get_collection").read_text()
)


@patch(
    "journeys.validators.comparers.get_all_dbs_raw", MagicMock(return_value=stub),
)
def test_get_dbs_from_devices(bigip_mock, velos_mock):
    dbs = get_dbs_from_devices(bigip_mock, velos_mock)
    assert type(dbs) == list
    assert len(dbs) == 2
    bigip_db, velos_db = dbs[0], dbs[1]
    assert bigip_db == velos_db


@patch(
    "journeys.validators.comparers.get_dbs_from_devices",
    MagicMock(return_value=[stub, stub]),
)
def test_compare_db(bigip_mock, velos_mock):
    db_diff = compare_db(bigip_mock, velos_mock)
    assert type(db_diff) == DeepDiff
    assert not db_diff


def test_get_modules_footprint_from_devices(bigip_mock, velos_mock):
    diff = get_modules_footprint_from_devices(bigip_mock, velos_mock)
    assert type(diff) == list
    assert len(diff) == 2
    bigip_db, velos_db = diff[0], diff[1]
    assert bigip_db == velos_db


def test_compare_memory_footprint(bigip_mock, velos_mock):
    diff = compare_memory_footprint(bigip_mock, velos_mock)
    assert type(diff) == DeepDiff
    assert not diff


def test_compare_ciphersuites(bigip_mock, velos_mock):
    diff = compare_ciphersuites(bigip_mock, velos_mock)
    assert type(diff) == DeepDiff
    assert not diff
