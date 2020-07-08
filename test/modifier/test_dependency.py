import pytest

from journeys.modifier.dependency import Config
from journeys.modifier.dependency import FieldToFieldDependency
from journeys.modifier.dependency import FieldToNameDependency
from journeys.modifier.dependency import SubCollectionDependency
from journeys.modifier.dependency import build_dependency_map


def test_field_to_name_dependency():
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

    result = FieldToNameDependency(
        field_name="monitor", type_matcher=("ltm", "monitor")
    ).find(objects=objects, obj=pool)

    assert len(result) == 1
    assert result[0] == monitor_id


def test_field_to_field_dependency():
    config_string = """
ltm node /Common/192.168.0.100 {
    address 192.168.0.100
}

# that is a fake object (pool member does not exists as a top level object
ltm pool_member /Common/192.168.0.100:1025 {
    address 192.168.0.100
}
    """

    config = Config.from_string(string=config_string)

    objects = config.fields
    pool_member_id = "ltm pool_member /Common/192.168.0.100:1025"
    pool_member = objects.get(pool_member_id)

    node_id = "ltm node /Common/192.168.0.100"

    result = FieldToFieldDependency(
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
        dependency=FieldToNameDependency(
            field_name="monitor", type_matcher=("ltm", "monitor")
        ),
    ).find(objects=objects, obj=pool)

    assert len(result) == 1
    assert result[0] == monitor_id


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
            FieldToNameDependency(
                field_name="monitor", type_matcher=("ltm", "monitor")
            ),
            SubCollectionDependency(
                field_name="members",
                dependency=FieldToFieldDependency(
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
                dependency=FieldToNameDependency(
                    field_name="monitor", type_matcher=("ltm", "monitor")
                ),
            ),
        )

    result = build_dependency_map(config=config, dependencies_matrix=dependencies)

    pool_id = "ltm pool /Common/test_pool"
    monitor_id = "ltm monitor tcp /Common/tcp_custom"
    node_id = "ltm node /Common/192.168.0.100"

    assert len(result) == 1
    assert result[pool_id] == {monitor_id, node_id}
