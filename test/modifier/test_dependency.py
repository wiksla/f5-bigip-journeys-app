import pytest

from journeys.modifier.dependency import Config
from journeys.modifier.dependency import FieldKeyToNameDependency
from journeys.modifier.dependency import FieldValueToFieldValueDependency
from journeys.modifier.dependency import FieldValueToNameDependency
from journeys.modifier.dependency import NameToNameDependency
from journeys.modifier.dependency import SubCollectionDependency
from journeys.modifier.dependency import build_dependency_map


def test_field_value_to_name_dependency():
    config_string = """
ltm monitor tcp /Common/tcp_custom {
}

ltm pool /Common/test_pool {
    monitor /Common/tcp_custom
}
    """

    config = Config.from_string(string=config_string)

    objects = config.fields
    pool_id = "ltm pool /Common/test_pool"
    pool = objects.get(pool_id)

    monitor_id = "ltm monitor tcp /Common/tcp_custom"

    result = FieldValueToNameDependency(
        field_name="monitor", type_matcher=("ltm", "monitor")
    ).find(objects=objects, obj=pool)

    assert len(result) == 1
    assert result[0] == monitor_id


def test_field_value_to_field_value_dependency():
    config_string = """
ltm node /Common/192.168.0.100 {
    address 192.168.0.100
}

# that is a fake object (pool member does not exists as a top level object)
ltm pool_member /Common/192.168.0.100:1025 {
    address 192.168.0.100
}
    """

    config = Config.from_string(string=config_string)

    objects = config.fields
    pool_member_id = "ltm pool_member /Common/192.168.0.100:1025"
    pool_member = objects.get(pool_member_id)

    node_id = "ltm node /Common/192.168.0.100"

    result = FieldValueToFieldValueDependency(
        field_name="address", type_matcher=("ltm", "node"), target_field_name="address",
    ).find(objects=objects, obj=pool_member)

    assert len(result) == 1
    assert result[0] == node_id


def test_subcollection_dependency():
    config_string = """
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

    config = Config.from_string(string=config_string)

    objects = config.fields
    pool_id = "ltm pool /Common/test_pool"
    pool = objects.get(pool_id)

    monitor_id = "ltm monitor tcp /Common/tcp_custom"

    result = SubCollectionDependency(
        field_name="members",
        dependency=FieldValueToNameDependency(
            field_name="monitor", type_matcher=("ltm", "monitor")
        ),
    ).find(objects=objects, obj=pool)

    assert len(result) == 1
    assert result[0] == monitor_id


def test_field_key_to_name_dependency():
    config_string = """
net vlan /Common/virtWire_vlan_4096_1_353 {
}

net vlan-group /Common/virtWire {
    members {
        /Common/virtWire_vlan_4096_1_353
    }
}
    """

    config = Config.from_string(string=config_string)

    objects = config.fields
    vlan_group_id = "net vlan-group /Common/virtWire"
    vlan_group = objects.get(vlan_group_id)

    vlan_id = "net vlan /Common/virtWire_vlan_4096_1_353"

    result = SubCollectionDependency(
        field_name="members",
        dependency=FieldKeyToNameDependency(type_matcher=("net", "vlan")),
    ).find(objects=objects, obj=vlan_group)

    assert len(result) == 1
    assert result[0] == vlan_id


def test_name_to_name_dependency():
    config_string = """
net vlan /Common/virtWire_vlan_4096_1_353 {
}

net fdb vlan /Common/virtWire_vlan_4096_1_353 {
}
    """

    config = Config.from_string(string=config_string)

    objects = config.fields
    vlan_id = "net vlan /Common/virtWire_vlan_4096_1_353"
    vlan = objects.get(vlan_id)

    fdb_vlan_id = "net fdb vlan /Common/virtWire_vlan_4096_1_353"

    result = NameToNameDependency(type_matcher=("net", "fdb", "vlan")).find(
        objects=objects, obj=vlan
    )

    assert len(result) == 1
    assert result[0] == fdb_vlan_id


@pytest.mark.parametrize(
    "test_deduplication", [False, True],
)
def test_build_dependencies_map(test_deduplication):
    config_string = f"""
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

    config = Config.from_string(string=config_string)

    dependencies = {
        ("ltm", "pool"): [
            FieldValueToNameDependency(
                field_name="monitor", type_matcher=("ltm", "monitor")
            ),
            SubCollectionDependency(
                field_name="members",
                dependency=FieldValueToFieldValueDependency(
                    field_name="address",
                    type_matcher=("ltm", "node"),
                    target_field_name="address",
                ),
            ),
        ]
    }

    if test_deduplication:
        dependencies[("ltm", "pool")].append(
            SubCollectionDependency(
                field_name="members",
                dependency=FieldValueToNameDependency(
                    field_name="monitor", type_matcher=("ltm", "monitor")
                ),
            ),
        )

    result = build_dependency_map(config=config, dependencies_matrix=dependencies)

    pool_id = "ltm pool /Common/test_pool"
    monitor_id = "ltm monitor tcp /Common/tcp_custom"
    node_id = "ltm node /Common/192.168.0.100"

    assert len(result.forward) == 1
    assert len(result.reverse) == 2
    assert result.forward[pool_id] == {monitor_id, node_id}
    assert result.reverse[monitor_id] == {pool_id}
    assert result.reverse[node_id] == {pool_id}


def test_build_dependencies_map_net_module():
    config_string = """
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

    config = Config.from_string(string=config_string)

    result = build_dependency_map(config=config)

    assert len(result.forward) == 7

    assert result.forward["net vlan-group /Common/virtWire"] == {
        "net vlan /Common/virtWire_vlan_4096_1_353",
        "net vlan /Common/virtWire_vlan_4096_2_354",
    }

    assert result.forward["net vlan /Common/virtWire_vlan_4096_1_353"] == {
        "net fdb vlan /Common/virtWire_vlan_4096_1_353",
        "net trunk trunk_external",
    }

    assert result.forward["net vlan /Common/virtWire_vlan_4096_2_354"] == {
        "net fdb vlan /Common/virtWire_vlan_4096_2_354",
        "net trunk trunk_internal",
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

    assert len(result.reverse) == 11

    assert result.reverse["net trunk trunk_internal"] == {
        "net stp /Common/cist",
        "net vlan /Common/virtWire_vlan_4096_2_354",
    }
    assert result.reverse["net trunk trunk_external"] == {
        "net vlan /Common/virtWire_vlan_4096_1_353",
        "net stp /Common/cist",
    }
    assert result.reverse["net vlan /Common/virtWire_vlan_4096_2_354"] == {
        "net vlan-group /Common/virtWire",
        "net route-domain /Common/0",
        "net stp /Common/cist",
    }
    assert result.reverse["net vlan /Common/virtWire_vlan_4096_1_353"] == {
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
    assert result.reverse["net fdb vlan /Common/virtWire_vlan_4096_2_354"] == {
        "net vlan /Common/virtWire_vlan_4096_2_354"
    }
    assert result.reverse["net fdb vlan /Common/virtWire_vlan_4096_1_353"] == {
        "net vlan /Common/virtWire_vlan_4096_1_353"
    }
