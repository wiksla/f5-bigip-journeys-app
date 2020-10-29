from deepdiff import DeepDiff

from journeys.validators.helpers import pretty
from journeys.validators.helpers import tmsh_compare


def test_pretty_lists():
    aa = [1, 2, 3, 4]
    bb = [1, 2, 5]
    diff = DeepDiff(aa, bb)
    unique_name = "unique_name"
    unique_collection_name = "unique_collection_name"

    lines = pretty(diff, unique_name, unique_collection_name).splitlines()
    assert all([line.startswith(unique_name) for line in lines])
    assert lines[0].endswith(unique_collection_name + ".")
    assert not lines[1].endswith(unique_collection_name + ".")


def test_pretty_dicts():
    aa = {
        "tam": None,
        "vcmp": None,
        "pem": None,
        "host": {"memory": {"value": 7558}, "disk": {"value": 298859}},
        "tmos": {"memory": {"value": 89068}, "host-memory": {"value": 420}},
    }
    bb = {
        "host": {"memory": {"value": 1396}, "disk": {"value": 45920}},
        "tmos": {"memory": {"value": 6084}, "host-memory": {"value": 0}},
    }
    diff = DeepDiff(aa, bb)
    unique_name = "unique_name"
    unique_collection_name = "unique_collection_name"

    lines = pretty(diff, unique_name, unique_collection_name).splitlines()
    assert all([line.startswith(unique_name) for line in lines])
    assert all([line.endswith(unique_collection_name + ".") for line in lines[:3]])


def test_compare_tmsh_show_sys_soft(bigip_mock, velos_mock):
    cmd = "tmsh show sys software status"
    aaa = tmsh_compare(cmd, bigip_mock, velos_mock)
    assert type(aaa) == str
