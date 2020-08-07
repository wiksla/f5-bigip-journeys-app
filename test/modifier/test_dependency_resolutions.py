from unittest.mock import MagicMock

import pytest

import journeys.modifier.dependency as dp
from journeys.config import Config


@pytest.fixture
def dependency_conf():
    config_string = """
#TMSH 12.1.2
ltm node /Common/test_node {
    address 10.0.1.1
}
ltm monitor tcp /Common/tcp_custom {
}
ltm pool /Common/test_pool {
    monitor /Common/tcp_custom
}
ltm pool /Common/test_pool2 {
    members {
        /Common/10.0.0.1:0 {
            address 10.0.0.1
            monitor /Common/tcp_custom
        }
        /Common/10.0.0.2:0 {
            address 11.0.0.1
            monitor /Common/tcp_custom
        }
    }
}
# fake object for testing
ltm pool_member /Common/test_member {
    address 10.0.1.1
}
net fdb vlan /Common/vlan {
}
net vlan /Common/vlan {
}
net vlan-group /Common/vlan-group {
    members {
        /Common/vlan
    }
}
security nat policy /Common/policy {
    next-hop {
        vlan /Common/vlan
    }
}"""
    return Config.from_string(config_string)


def test_resolution_created_for_all_dependencies(dependency_conf):
    deps = dp.build_dependency_map(dependency_conf)
    for id_from, list_to in deps.reverse.items():
        for id_to in list_to:
            assert (id_to, id_from) in deps.resolutions


def test_field_value_to_name_dependency_resolution(dependency_conf):

    matrix = {
        ("ltm", "pool"): [
            dp.FieldValueToNameDependency(
                field_name="monitor", type_matcher=("ltm", "monitor")
            )
        ]
    }

    deps = dp.build_dependency_map(dependency_conf, matrix)

    assert "monitor" in dependency_conf.fields["ltm pool /Common/test_pool"].fields
    deps.resolutions[
        ("ltm pool /Common/test_pool", "ltm monitor tcp /Common/tcp_custom")
    ](dependency_conf)
    assert "monitor" not in dependency_conf.fields["ltm pool /Common/test_pool"].fields


def test_field_value_to_field_value_dependency_delete_child_resolution(dependency_conf):

    matrix = {
        ("ltm", "pool_member"): [
            dp.FieldValueToFieldValueDependency(
                field_name="address",
                type_matcher=("ltm", "node"),
                target_field_name="address",
            )
        ]
    }

    deps = dp.build_dependency_map(dependency_conf, matrix)

    assert (
        "address"
        in dependency_conf.fields["ltm pool_member /Common/test_member"].fields
    )
    deps.resolutions[
        ("ltm pool_member /Common/test_member", "ltm node /Common/test_node")
    ](dependency_conf)
    assert (
        "address"
        not in dependency_conf.fields["ltm pool_member /Common/test_member"].fields
    )


def test_field_value_to_field_value_dependency_delete_self_resolution(dependency_conf):

    matrix = {
        ("ltm", "pool_member"): [
            dp.FieldValueToFieldValueDependency(
                field_name="address",
                type_matcher=("ltm", "node"),
                target_field_name="address",
                resolution="delete_self",
            )
        ]
    }

    deps = dp.build_dependency_map(dependency_conf, matrix)

    assert "ltm pool_member /Common/test_member" in dependency_conf.fields
    deps.resolutions[
        ("ltm pool_member /Common/test_member", "ltm node /Common/test_node")
    ](dependency_conf)
    assert "ltm pool_member /Common/test_member" not in dependency_conf.fields


def test_subcollection_dependency_nested_resolution(dependency_conf):

    fake_resolution = MagicMock()
    fake_dependency = MagicMock()
    fake_dependency.find.return_value = ["ltm monitor tcp /Common/tcp_custom"]
    fake_dependency.get_resolve.return_value = fake_resolution
    matrix = {
        ("ltm", "pool"): [
            dp.SubCollectionDependency(
                field_name="members", dependency=fake_dependency,
            )
        ]
    }

    deps = dp.build_dependency_map(dependency_conf, matrix)

    deps.resolutions[
        ("ltm pool /Common/test_pool2", "ltm monitor tcp /Common/tcp_custom")
    ](dependency_conf)
    fake_dependency.get_resolve.assert_called()
    fake_resolution.assert_called()
    assert fake_resolution.call_count == 2  # one for each member


def test_subcollection_dependency_delete_resolution(dependency_conf):
    fake_resolution = MagicMock()
    fake_dependency = MagicMock()
    fake_dependency.find.return_value = ["ltm monitor tcp /Common/tcp_custom"]
    fake_dependency.get_resolve.return_value = fake_resolution
    matrix = {
        ("ltm", "pool"): [
            dp.SubCollectionDependency(
                field_name="members", dependency=fake_dependency, resolution="delete"
            )
        ]
    }

    deps = dp.build_dependency_map(dependency_conf, matrix)

    assert "members" in dependency_conf.fields["ltm pool /Common/test_pool2"].fields
    deps.resolutions[
        ("ltm pool /Common/test_pool2", "ltm monitor tcp /Common/tcp_custom")
    ](dependency_conf)
    fake_resolution.assert_not_called()
    assert "members" not in dependency_conf.fields["ltm pool /Common/test_pool2"].fields


def test_nested_dependency_nested_resolution(dependency_conf):

    fake_resolution = MagicMock()
    fake_dependency = MagicMock()
    fake_dependency.find.return_value = ["net vlan /Common/vlan"]
    fake_dependency.get_resolve.return_value = fake_resolution
    matrix = {
        ("security", "nat", "policy"): [
            dp.NestedDependency(field_name="next-hop", dependency=fake_dependency,)
        ]
    }

    deps = dp.build_dependency_map(dependency_conf, matrix)
    deps.resolutions[("security nat policy /Common/policy", "net vlan /Common/vlan")](
        dependency_conf
    )

    fake_dependency.get_resolve.assert_called()
    fake_resolution.assert_called_once()


def test_nested_dependency_delete_resolution(dependency_conf):
    fake_resolution = MagicMock()
    fake_dependency = MagicMock()
    fake_dependency.find.return_value = ["net vlan /Common/vlan"]
    fake_dependency.get_resolve.return_value = fake_resolution
    matrix = {
        ("security", "nat", "policy"): [
            dp.NestedDependency(
                field_name="next-hop", dependency=fake_dependency, resolution="delete"
            )
        ]
    }

    deps = dp.build_dependency_map(dependency_conf, matrix)

    assert (
        "next-hop"
        in dependency_conf.fields["security nat policy /Common/policy"].fields
    )
    deps.resolutions[("security nat policy /Common/policy", "net vlan /Common/vlan")](
        dependency_conf
    )
    fake_resolution.assert_not_called()
    assert (
        "next-hop"
        not in dependency_conf.fields["security nat policy /Common/policy"].fields
    )


def test_name_to_name_dependency_resolution(dependency_conf):

    matrix = {
        ("net", "fdb", "vlan"): [dp.NameToNameDependency(type_matcher=("net", "vlan"))]
    }

    deps = dp.build_dependency_map(dependency_conf, matrix)

    assert "net fdb vlan /Common/vlan" in dependency_conf.fields
    deps.resolutions[("net fdb vlan /Common/vlan", "net vlan /Common/vlan")](
        dependency_conf
    )
    assert "net fdb vlan /Common/vlan" not in dependency_conf.fields
