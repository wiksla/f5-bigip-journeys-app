import os
from unittest.mock import patch

import pytest

from journeys import config
from journeys.errors import BigDbError

RESOURCES_DIR = os.path.join(os.path.dirname(__file__), "resources")


@pytest.fixture
def config_file():
    return os.path.join(RESOURCES_DIR, "sample_bigip.conf")


@pytest.fixture
def conf(config_file):
    return config.Config.from_conf(config_file)


def test_config_load_from_string(config_file):
    with open(config_file, "r") as f:
        content = f.read()
    conf = config.Config.from_string(content)
    assert isinstance(conf, config.Config)
    assert conf.data


def test_config_load_from_file(conf):
    assert isinstance(conf, config.Config)
    assert conf.data


@patch("builtins.open")
def test_config_build_to_file(mock_open, conf):
    filename = conf.data["config"][0]["file"]
    conf.build()
    assert filename in mock_open.call_args[0][0]
    mock_open().write.assert_called()


@pytest.mark.parametrize(
    "query,key",
    [
        (2, "ltm node /Common/node"),
        (("wom",), "wom deduplication"),
        (("ltm", "virtual"), "ltm virtual /Common/virtual"),
        ("wom endpoint-discovery", "wom endpoint-discovery"),
    ],
)
def test_get_field(conf, query, key):
    field = conf.fields.get(query)
    assert field.key == key
    field = conf.fields[query]
    assert field.key == key


def test_get_field_not_found(conf):
    with pytest.raises(KeyError):
        conf.fields.get("fake field")


@pytest.mark.parametrize(
    "query, items", [(("wom",), 2), (("ltm", "virtual"), 1), (("fake", "field"), 0)]
)
def test_get_all_fields(query, items, conf):
    fields = conf.fields.get_all(query)
    assert len(list(fields)) == items


def test_get_re(conf):
    field = conf.fields.get_re(".* virtual .*")
    assert field.key == "ltm virtual /Common/virtual"


def test_get_re_not_found(conf):
    with pytest.raises(KeyError):
        conf.fields.get_re("fake .*")


def test_get_all_re(conf):
    fields = conf.fields.get_all_re(".tm .*")
    assert len(list(fields)) == 4


def test_top_field_key_is_id(conf):
    field = conf.fields.get(("ltm", "node"))
    assert field.key == field.id


def test_fields_contains(conf):
    assert "ltm virtual /Common/virtual" in conf.fields
    assert ("ltm", "node") in conf.fields
    assert ("address") in conf.fields["ltm node /Common/node"].fields


def test_add_field(conf):
    assert "fake field /Common/fake" not in conf.fields
    conf.fields.add(
        ("fake", "field", "/Common/fake"), block=True, file="sample_bigip.conf"
    )
    assert "fake field /Common/fake" in conf.fields
    assert conf.fields[("fake", "field", "/Common/fake")].fields is not None


def test_add_nested_field(conf):
    node = conf.fields[("ltm", "node", "/Common/node")]
    assert "test" not in node.fields
    node.fields.add(("test", "value"))
    assert "test" in node.fields
    assert node.fields["test"].value == "value"
    assert node.fields["test"].fields is None


def test_create_block(conf):
    virtual = conf.fields[("ltm", "virtual", "/Common/virtual")]
    assert virtual.fields["ip-forward"].fields is None
    virtual.fields["ip-forward"].create_block()
    assert virtual.fields["ip-forward"].fields is not None


def test_delete_block(conf):
    virtual = conf.fields[("ltm", "virtual", "/Common/virtual")]
    assert virtual.fields["vlans"].fields is not None
    virtual.fields["vlans"].delete_block()
    assert virtual.fields["vlans"].fields is None


@pytest.mark.parametrize(
    "item", [2, ("ltm",), ("ltm", "virtual"), "wom endpoint-discovery"],
)
def test_lookup_after_delete(conf, item):

    conf.fields.get(item).delete()

    try:
        field_no_lookup = conf.fields.get(item, lookup=False)
    except KeyError:
        field_no_lookup = "exception"
    try:
        field_lookup = conf.fields.get(item, lookup=True)
    except KeyError:
        field_lookup = "exception"

    assert field_no_lookup == field_lookup


@pytest.mark.parametrize(
    "item,id",
    [
        (("ltm", "rule", "testrule"), "ltm rule testrule"),
        (("ltm", "testfield"), "ltm testfield"),
    ],
)
def test_lookup_after_add(conf, item, id):
    conf.fields.add(item, file="sample_bigip.conf")
    assert conf.fields.get(item, lookup=True) == conf.fields.get(item, lookup=False)
    assert conf.fields.get(id, lookup=True) == conf.fields.get(id, lookup=False)


def test_lookup_after_update(conf):
    virtual = conf.fields.get("ltm virtual /Common/virtual")
    virtual.args = ("ltm", "test", "/Common/virtual")
    with pytest.raises(KeyError):
        conf.fields.get("ltm virtual /Common/virtual", lookup=True)
    with pytest.raises(KeyError):
        conf.fields.get(("ltm", "virtual", "/Common/virtual"), lookup=True)
    assert conf.fields.get(("ltm", "test"), lookup=True) == conf.fields.get(
        "ltm test /Common/virtual", lookup=True
    )


@pytest.mark.parametrize(
    "in_val,out_val", [("val", "val"), (None, ""), (["val1", "val2"], "val1 val2")]
)
def test_update_value(in_val, out_val, conf):
    node = conf.fields[("ltm", "node", "/Common/node")]
    assert node.fields["address"].value != out_val
    node.fields["address"].value = in_val
    assert node.fields["address"].value == out_val


def test_delete_field(conf):
    tag = ("ltm", "node")
    assert tag in conf.fields
    conf.fields[tag].delete()
    assert tag not in conf.fields


def test_convert_field_to_comments(conf):
    tag = ("ltm", "node")
    assert tag in conf.fields
    node = conf.fields[tag]
    index = conf.fields.index(node)
    assert not conf.fields[index].key.startswith("#")
    node.convert_to_comments()
    assert tag not in conf.fields
    assert conf.fields[index].key.startswith("#")


def test_obtain_bigdb_parameter(bigdb_dat):
    bigdb_dat.FILENAME = "sample_BigDB.dat"
    bigdb_dat_config = bigdb_dat(dirname=RESOURCES_DIR)
    assert (
        bigdb_dat_config.get(section="Cluster.MgmtIpaddr", option="scf_config")
        == "false"
    )


def test_big_db_with_duplicated_section(bigdb_dat):
    bigdb_dat.FILENAME = "sample_BigDB_duplicate_section.dat"
    with pytest.raises(BigDbError):
        bigdb_dat(dirname=RESOURCES_DIR)


def test_big_db_with_duplicated_option(bigdb_dat):
    bigdb_dat.FILENAME = "sample_BigDB_duplicate_option.dat"
    with pytest.raises(BigDbError):
        bigdb_dat(dirname=RESOURCES_DIR)


@pytest.fixture
def bigdb_dat():
    yield config.BigDB
    config.BigDB.FILENAME = "BigDB.dat"
