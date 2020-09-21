import pytest

config = """
net vlan /Common/vlan1 {
    cmp-hash src-ip
    tag 4094
}

net vlan /Common/vlan4 {
    cmp-hash dst-ip
    tag 4094
}
"""

CONFLICT_NAME = "SPDAG"


def test_spdag_delete(test_solution):
    solution_name = "SPDAG_delete_objects"

    controller = test_solution(
        conflict_name=CONFLICT_NAME, solution_name=solution_name, conf_file=config,
    )

    with pytest.raises(KeyError, match=r"Requested key.*not found"):
        controller.config.fields.get(("net", "vlan"))


def test_spdag_change(test_solution):
    solution_name = "F5_Recommended_SPDAG_change_value_to_default"

    controller = test_solution(
        conflict_name=CONFLICT_NAME, solution_name=solution_name, conf_file=config,
    )

    node = controller.config.fields["net vlan /Common/vlan4"]
    assert node.fields["cmp-hash"].value == "default"
    node = controller.config.fields["net vlan /Common/vlan1"]
    assert node.fields["cmp-hash"].value == "default"
