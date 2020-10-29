from deepdiff import DeepDiff

from journeys.validators.module_footprint_comparer import compare_memory_footprint
from journeys.validators.module_footprint_comparer import (
    get_modules_footprint_from_devices,
)


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
