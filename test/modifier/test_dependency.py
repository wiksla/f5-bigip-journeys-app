import pytest

from journeys.modifier.dependency import Config
from journeys.modifier.dependency import DependencyMap
from journeys.modifier.dependency import FieldKeyToNameDependency
from journeys.modifier.dependency import FieldValueToFieldValueDependency
from journeys.modifier.dependency import FieldValueToNameDependency
from journeys.modifier.dependency import NameToNameDependency
from journeys.modifier.dependency import NestedDependency
from journeys.modifier.dependency import SubCollectionDependency


def test_field_value_to_name_dependency():
    config = """
ltm monitor tcp /Common/tcp_custom {
}

ltm pool /Common/test_pool {
    monitor /Common/tcp_custom
}
    """

    config = Config.from_string(string=config)

    pool = config.fields.get("ltm pool /Common/test_pool")
    monitor = config.fields.get("ltm monitor tcp /Common/tcp_custom")
    dep = FieldValueToNameDependency(
        child_types=[("ltm", "pool")],
        field_name="monitor",
        parent_types=[("ltm", "monitor")],
    )
    assert list(dep.match_parent(monitor))
    assert next(dep.match_parent(monitor)) == "/Common/tcp_custom"
    assert not list(dep.match_child(monitor))

    assert list(dep.match_child(pool))
    assert next(dep.match_child(pool)) == "/Common/tcp_custom"
    assert not list(dep.match_parent(pool))


def test_field_value_to_field_value_dependency():
    config = """
ltm node /Common/192.168.0.100 {
    address 192.168.0.100
}

# that is a fake object (pool member does not exists as a top level object)
ltm pool_member /Common/192.168.0.100:1025 {
    address 192.168.0.100
}
    """

    config = Config.from_string(string=config)

    objects = config.fields
    pool_member = objects.get("ltm pool_member /Common/192.168.0.100:1025")
    node = objects.get("ltm node /Common/192.168.0.100")

    dep = FieldValueToFieldValueDependency(
        child_types=[("ltm", "pool_member")],
        field_name="address",
        parent_types=[("ltm", "node")],
        target_field_name="address",
    )

    assert list(dep.match_parent(node))
    assert next(dep.match_parent(node)) == "192.168.0.100"
    assert not list(dep.match_child(node))

    assert list(dep.match_child(pool_member))
    assert next(dep.match_child(pool_member)) == "192.168.0.100"
    assert not list(dep.match_parent(pool_member))


def test_subcollection_dependency():
    config = """
ltm monitor tcp /Common/tcp_custom {
}

ltm pool /Common/test_pool {
    members {
        /Common/198.18.210.129:0 {
            address 198.18.210.129
            monitor /Common/tcp_custom
        }
    }
}
    """

    config = Config.from_string(string=config)

    objects = config.fields
    pool = objects.get("ltm pool /Common/test_pool")
    monitor = objects.get("ltm monitor tcp /Common/tcp_custom")

    dep = SubCollectionDependency(
        child_types=[("ltm", "pool")],
        field_name="members",
        parent_types=[("ltm", "monitor")],
        dependency=FieldValueToNameDependency(field_name="monitor"),
    )

    assert list(dep.match_parent(monitor))
    assert next(dep.match_parent(monitor)) == "/Common/tcp_custom"
    assert not list(dep.match_child(monitor))

    assert list(dep.match_child(pool))
    assert next(dep.match_child(pool)) == "/Common/tcp_custom"
    assert not list(dep.match_parent(pool))


def test_field_key_to_name_dependency():
    config = """
net vlan /Common/vlan {
}

net vlan-group /Common/group {
    members {
        /Common/vlan
    }
}
    """

    config = Config.from_string(string=config)

    objects = config.fields
    vlan_group = objects.get("net vlan-group /Common/group")
    vlan = objects.get("net vlan /Common/vlan")

    dep = SubCollectionDependency(
        child_types=[("net", "vlan-group")],
        field_name="members",
        parent_types=[("net", "vlan")],
        dependency=FieldKeyToNameDependency(),
    )

    assert list(dep.match_parent(vlan))
    assert next(dep.match_parent(vlan)) == "/Common/vlan"
    assert not list(dep.match_child(vlan))

    assert list(dep.match_child(vlan_group))
    assert next(dep.match_child(vlan_group)) == "/Common/vlan"
    assert not list(dep.match_parent(vlan_group))


def test_nested_dependency():
    config = """
net vlan /Common/test_vlan {
}
security nat policy /Common/test_policy {
    next-hop {
        vlan /Common/test_vlan
    }
}
    """
    config = Config.from_string(string=config)

    objects = config.fields
    vlan = objects.get("net vlan /Common/test_vlan")
    policy = objects.get("security nat policy /Common/test_policy")

    dep = NestedDependency(
        child_types=[("security", "nat", "policy")],
        field_name="next-hop",
        parent_types=[("net", "vlan")],
        dependency=FieldValueToNameDependency(field_name="vlan"),
    )

    assert list(dep.match_parent(vlan))
    assert next(dep.match_parent(vlan)) == "/Common/test_vlan"
    assert not list(dep.match_child(vlan))

    assert list(dep.match_child(policy))
    assert next(dep.match_child(policy)) == "/Common/test_vlan"
    assert not list(dep.match_parent(policy))


def test_name_to_name_dependency():
    config = """
net vlan /Common/vlan {
}

net fdb vlan /Common/vlan {
}
    """

    config = Config.from_string(string=config)

    objects = config.fields
    vlan = objects.get("net vlan /Common/vlan")
    fdb_vlan = objects.get("net fdb vlan /Common/vlan")

    dep = NameToNameDependency(
        child_types=[("net", "fdb", "vlan")], parent_types=[("net", "vlan")]
    )

    assert list(dep.match_parent(vlan))
    assert next(dep.match_parent(vlan)) == "/Common/vlan"
    assert not list(dep.match_child(vlan))

    assert list(dep.match_child(fdb_vlan))
    assert next(dep.match_child(fdb_vlan)) == "/Common/vlan"
    assert not list(dep.match_parent(fdb_vlan))


@pytest.mark.parametrize(
    "test_deduplication", [False, True],
)
def test_build_dependencies_map(test_deduplication):
    config = f"""
ltm node /Common/192.168.0.100 {{
    address 192.168.0.100
}}

ltm monitor tcp /Common/tcp_custom {{
}}

ltm pool /Common/test_pool {{
    members {{
        /Common/192.168.0.100:0 {{
            address 192.168.0.100
            {"monitor /Common/tcp_custom" if test_deduplication else ""}
        }}
    }}
    monitor /Common/tcp_custom
}}
    """

    config = Config.from_string(string=config)

    dependencies = [
        FieldValueToNameDependency(
            child_types=[("ltm", "pool")],
            field_name="monitor",
            parent_types=[("ltm", "monitor")],
        ),
        SubCollectionDependency(
            child_types=[("ltm", "pool")],
            field_name="members",
            parent_types=[("ltm", "node")],
            dependency=FieldValueToFieldValueDependency(
                field_name="address", target_field_name="address",
            ),
        ),
    ]

    if test_deduplication:
        dependencies.append(
            SubCollectionDependency(
                child_types=[("ltm", "pool")],
                field_name="members",
                parent_types=[("ltm", "monitor")],
                dependency=FieldValueToNameDependency(field_name="monitor",),
            ),
        )

    result = DependencyMap(config=config, dependencies=dependencies)

    pool_id = "ltm pool /Common/test_pool"
    monitor_id = "ltm monitor tcp /Common/tcp_custom"
    node_id = "ltm node /Common/192.168.0.100"

    assert len(result.forward) == 1
    assert len(result.reverse) == 2
    assert result.forward[pool_id] == {monitor_id, node_id}
    assert result.reverse[monitor_id] == {pool_id}
    assert result.reverse[node_id] == {pool_id}


def test_build_dependencies_map_net_module():
    config = """
net stp /Common/cist {
    trunks {
        trunk_external {}
        trunk_internal {}
    }
    vlans {
        /Common/virtWire_vlan_4096_1_353
        /Common/virtWire_vlan_4096_2_354
    }
}

net interface 1.1 {}
net interface 1.2 {}
net interface 2.1 {}
net interface 2.2 {}

net route-domain /Common/0 {
    vlans {
        /Common/virtWire_vlan_4096_1_353
        /Common/virtWire_vlan_4096_2_354
        /Common/virtWire
    }
}

net trunk trunk_external {
    interfaces {
        2.1
        2.2
    }
}
net trunk trunk_internal {
    interfaces {
        1.1
        1.2
    }
}

net vlan /Common/virtWire_vlan_4096_1_353 {
    interfaces {
        trunk_external {}
    }
}
net vlan /Common/virtWire_vlan_4096_2_354 {
    interfaces {
        trunk_internal {}
    }
}

net vlan-group /Common/virtWire {
    members {
        /Common/virtWire_vlan_4096_1_353
        /Common/virtWire_vlan_4096_2_354
    }
}

net fdb vlan /Common/virtWire_vlan_4096_1_353 { }
net fdb vlan /Common/virtWire_vlan_4096_2_354 { }
    """

    config = Config.from_string(string=config)

    result = DependencyMap(config)

    # assert len(result.forward) == 9

    assert result.forward["net vlan-group /Common/virtWire"] == {
        "net vlan /Common/virtWire_vlan_4096_1_353",
        "net vlan /Common/virtWire_vlan_4096_2_354",
    }

    assert result.forward["net vlan /Common/virtWire_vlan_4096_1_353"] == {
        "net trunk trunk_external",
    }

    assert result.forward["net fdb vlan /Common/virtWire_vlan_4096_1_353"] == {
        "net vlan /Common/virtWire_vlan_4096_1_353",
    }

    assert result.forward["net vlan /Common/virtWire_vlan_4096_2_354"] == {
        "net trunk trunk_internal",
    }

    assert result.forward["net fdb vlan /Common/virtWire_vlan_4096_2_354"] == {
        "net vlan /Common/virtWire_vlan_4096_2_354",
    }

    assert result.forward["net trunk trunk_external"] == {
        "net interface 2.1",
        "net interface 2.2",
    }

    assert result.forward["net trunk trunk_internal"] == {
        "net interface 1.1",
        "net interface 1.2",
    }

    assert result.forward["net route-domain /Common/0"] == {
        "net vlan-group /Common/virtWire",
        "net vlan /Common/virtWire_vlan_4096_1_353",
        "net vlan /Common/virtWire_vlan_4096_2_354",
    }

    assert result.forward["net stp /Common/cist"] == {
        "net vlan /Common/virtWire_vlan_4096_1_353",
        "net vlan /Common/virtWire_vlan_4096_2_354",
        "net trunk trunk_external",
        "net trunk trunk_internal",
    }

    assert len(result.reverse) == 9

    assert result.reverse["net trunk trunk_internal"] == {
        "net stp /Common/cist",
        "net vlan /Common/virtWire_vlan_4096_2_354",
    }
    assert result.reverse["net trunk trunk_external"] == {
        "net vlan /Common/virtWire_vlan_4096_1_353",
        "net stp /Common/cist",
    }
    assert result.reverse["net vlan /Common/virtWire_vlan_4096_2_354"] == {
        "net fdb vlan /Common/virtWire_vlan_4096_2_354",
        "net vlan-group /Common/virtWire",
        "net route-domain /Common/0",
        "net stp /Common/cist",
    }
    assert result.reverse["net vlan /Common/virtWire_vlan_4096_1_353"] == {
        "net fdb vlan /Common/virtWire_vlan_4096_1_353",
        "net vlan-group /Common/virtWire",
        "net route-domain /Common/0",
        "net stp /Common/cist",
    }
    assert result.reverse["net vlan-group /Common/virtWire"] == {
        "net route-domain /Common/0"
    }
    assert result.reverse["net interface 1.2"] == {"net trunk trunk_internal"}
    assert result.reverse["net interface 1.1"] == {"net trunk trunk_internal"}
    assert result.reverse["net interface 2.2"] == {"net trunk trunk_external"}
    assert result.reverse["net interface 2.1"] == {"net trunk trunk_external"}
