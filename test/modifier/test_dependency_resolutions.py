from unittest.mock import MagicMock

import pytest

import journeys.modifier.dependency as dp
from journeys.config import Config


@pytest.fixture
def dependency_conf():
    config = """
#TMSH 12.1.2
cm device bigip1 {
    mirror-ip 10.11.12.13
    multicast-ip 10.11.12.13
}
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
net interface 1.0 {
}
net self test-self {
    address 10.11.12.13  # invalid - for test
}
net trunk test-trunk {
}
net vlan /Common/vlan {
    interfaces {
        1.0 { }
        test-trunk { }
    }
}
net vlan /Common/vlan2 {
    interfaces {
        test-trunk { }
    }
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
    return Config.from_string(config)


def test_resolution_created_for_all_dependencies(dependency_conf):
    deps = dp.DependencyMap(dependency_conf)
    for id_from, list_to in deps.reverse.items():
        for id_to in list_to:
            assert (id_to, id_from) in deps.resolutions


def test_field_value_to_name_dependency_resolution(dependency_conf):

    matrix = [
        dp.FieldValueToNameDependency(
            child_types=[("ltm", "pool")],
            field_name="monitor",
            parent_types=[("ltm", "monitor")],
        )
    ]

    deps = dp.DependencyMap(dependency_conf, matrix)

    assert "monitor" in dependency_conf.fields["ltm pool /Common/test_pool"].fields
    deps.apply_resolution(
        dependency_conf,
        "ltm pool /Common/test_pool",
        "ltm monitor tcp /Common/tcp_custom",
    )
    assert "monitor" not in dependency_conf.fields["ltm pool /Common/test_pool"].fields


def test_field_value_to_field_value_dependency_delete_child_resolution(dependency_conf):

    matrix = [
        dp.FieldValueToFieldValueDependency(
            child_types=[("ltm", "pool_member")],
            field_name="address",
            parent_types=[("ltm", "node")],
            target_field_name="address",
        )
    ]

    deps = dp.DependencyMap(dependency_conf, matrix)

    assert (
        "address"
        in dependency_conf.fields["ltm pool_member /Common/test_member"].fields
    )
    deps.apply_resolution(
        dependency_conf,
        "ltm pool_member /Common/test_member",
        "ltm node /Common/test_node",
    )
    assert (
        "address"
        not in dependency_conf.fields["ltm pool_member /Common/test_member"].fields
    )


def test_field_value_to_field_value_dependency_delete_self_resolution(dependency_conf):

    matrix = [
        dp.FieldValueToFieldValueDependency(
            child_types=[("ltm", "pool_member")],
            field_name="address",
            parent_types=[("ltm", "node")],
            target_field_name="address",
            resolution="delete_self",
        )
    ]

    deps = dp.DependencyMap(dependency_conf, matrix)

    assert "ltm pool_member /Common/test_member" in dependency_conf.fields
    deps.apply_resolution(
        dependency_conf,
        "ltm pool_member /Common/test_member",
        "ltm node /Common/test_node",
    )
    assert "ltm pool_member /Common/test_member" not in dependency_conf.fields


def test_subcollection_dependency_nested_resolution(dependency_conf):

    fake_resolution = MagicMock()
    fake_dependency = MagicMock()
    fake_dependency.get_resolve.return_value = fake_resolution
    fake_dependency.get_value.side_effect = lambda x: iter(["/Common/tcp_custom"])
    fake_dependency.get_target_value.side_effect = lambda x: iter(
        ["/Common/tcp_custom"]
    )
    matrix = [
        dp.SubCollectionDependency(
            child_types=[("ltm", "pool")],
            field_name="members",
            parent_types=[("ltm", "monitor")],
            dependency=fake_dependency,
        )
    ]

    deps = dp.DependencyMap(dependency_conf, matrix)

    deps.apply_resolution(
        dependency_conf,
        "ltm pool /Common/test_pool2",
        "ltm monitor tcp /Common/tcp_custom",
    )
    fake_dependency.get_resolve.assert_called()
    fake_resolution.assert_called()
    assert fake_resolution.call_count == 2  # one for each member


def test_subcollection_dependency_delete_resolution(dependency_conf):
    fake_resolution = MagicMock()
    fake_dependency = MagicMock()
    fake_dependency.get_resolve.return_value = fake_resolution
    fake_dependency.get_value.return_value = iter(["/Common/tcp_custom"])
    fake_dependency.get_target_value.return_value = iter(["/Common/tcp_custom"])
    matrix = [
        dp.SubCollectionDependency(
            child_types=[("ltm", "pool")],
            field_name="members",
            parent_types=[("ltm", "monitor")],
            dependency=fake_dependency,
            resolution="delete",
        )
    ]

    deps = dp.DependencyMap(dependency_conf, matrix)

    assert "members" in dependency_conf.fields["ltm pool /Common/test_pool2"].fields
    deps.apply_resolution(
        dependency_conf,
        "ltm pool /Common/test_pool2",
        "ltm monitor tcp /Common/tcp_custom",
    )
    fake_resolution.assert_not_called()
    assert "members" not in dependency_conf.fields["ltm pool /Common/test_pool2"].fields


def test_subcollection_dependency_nested_with_cleanup_resolution(dependency_conf):
    matrix = [
        dp.SubCollectionDependency(
            child_types=[("net", "vlan")],
            field_name="interfaces",
            dependency=dp.FieldKeyToNameDependency(),
            parent_types=[("net", "trunk")],
            resolution="nested_with_cleanup",
        ),
    ]

    deps = dp.DependencyMap(dependency_conf, matrix)
    assert "interfaces" in dependency_conf.fields["net vlan /Common/vlan"].fields
    deps.apply_resolution(
        dependency_conf, "net vlan /Common/vlan", "net trunk test-trunk"
    )
    assert "interfaces" in dependency_conf.fields["net vlan /Common/vlan"].fields

    assert "interfaces" in dependency_conf.fields["net vlan /Common/vlan2"].fields
    deps.apply_resolution(
        dependency_conf, "net vlan /Common/vlan2", "net trunk test-trunk"
    )
    assert "interfaces" not in dependency_conf.fields["net vlan /Common/vlan2"].fields


def test_nested_dependency_nested_resolution(dependency_conf):

    fake_resolution = MagicMock()
    fake_dependency = MagicMock()
    fake_dependency.get_resolve.return_value = fake_resolution
    fake_dependency.get_value.return_value = iter(["/Common/vlan"])
    fake_dependency.get_target_value.return_value = iter(["/Common/vlan"])
    matrix = [
        dp.NestedDependency(
            child_types=[("security", "nat", "policy")],
            field_name="next-hop",
            dependency=fake_dependency,
            parent_types=[("net", "vlan")],
        )
    ]

    deps = dp.DependencyMap(dependency_conf, matrix)
    deps.apply_resolution(
        dependency_conf, "security nat policy /Common/policy", "net vlan /Common/vlan"
    )

    fake_dependency.get_resolve.assert_called()
    fake_resolution.assert_called_once()


def test_nested_dependency_delete_resolution(dependency_conf):
    fake_resolution = MagicMock()
    fake_dependency = MagicMock()
    fake_dependency.get_resolve.return_value = fake_resolution
    fake_dependency.get_value.return_value = iter(["/Common/vlan"])
    fake_dependency.get_target_value.return_value = iter(["/Common/vlan"])
    matrix = [
        dp.NestedDependency(
            child_types=[("security", "nat", "policy")],
            field_name="next-hop",
            dependency=fake_dependency,
            parent_types=[("net", "vlan")],
            resolution="delete",
        )
    ]

    deps = dp.DependencyMap(dependency_conf, matrix)

    assert (
        "next-hop"
        in dependency_conf.fields["security nat policy /Common/policy"].fields
    )
    deps.apply_resolution(
        dependency_conf, "security nat policy /Common/policy", "net vlan /Common/vlan"
    )
    fake_resolution.assert_not_called()
    assert (
        "next-hop"
        not in dependency_conf.fields["security nat policy /Common/policy"].fields
    )


def test_name_to_name_dependency_resolution(dependency_conf):

    matrix = [
        dp.NameToNameDependency(
            child_types=[("net", "fdb", "vlan")], parent_types=[("net", "vlan")]
        )
    ]

    deps = dp.DependencyMap(dependency_conf, matrix)

    assert "net fdb vlan /Common/vlan" in dependency_conf.fields
    deps.apply_resolution(
        dependency_conf, "net fdb vlan /Common/vlan", "net vlan /Common/vlan"
    )
    assert "net fdb vlan /Common/vlan" not in dependency_conf.fields


def test_two_objects_multiple_dependencies_resolutions(dependency_conf):
    matrix = [
        dp.FieldValueToFieldValueDependency(
            child_types=[("cm", "device")],
            field_name="mirror-ip",
            parent_types=[("net", "self")],
            target_field_name="address",
        ),
        dp.FieldValueToFieldValueDependency(
            child_types=[("cm", "device")],
            field_name="multicast-ip",
            parent_types=[("net", "self")],
            target_field_name="address",
        ),
    ]

    deps = dp.DependencyMap(dependency_conf, matrix)

    assert "mirror-ip" in dependency_conf.fields["cm device bigip1"].fields
    assert "multicast-ip" in dependency_conf.fields["cm device bigip1"].fields
    deps.apply_resolution(dependency_conf, "cm device bigip1", "net self test-self")
    assert "mirror-ip" not in dependency_conf.fields["cm device bigip1"].fields
    assert "multicast-ip" not in dependency_conf.fields["cm device bigip1"].fields
