import os
from unittest.mock import patch

import pytest

from journeys import config


@pytest.fixture
def config_file():
    relative = "resources/sample_bigip.conf"
    path = os.path.join(os.path.dirname(__file__), relative)
    return path


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
