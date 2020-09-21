import pytest

config = """
net vlan /Common/vlan_external_az {
    customer-tag 6969
    description "External VLAN with default tag and customer tag (double tagging)"
    interfaces {
        1.1 { }
    }
    sflow {
        poll-interval-global no     Object exists
        sampling-rate-global no
    }
    tag 4094
}
"""


CONFLICT_NAME = "DoubleTagging"


def test_double_tagging_delete(test_solution):
    solution_name = "F5_Recommended_DoubleTagging_delete_objects"

    controller = test_solution(
        conflict_name=CONFLICT_NAME, solution_name=solution_name, conf_file=config,
    )

    with pytest.raises(KeyError, match=r"Requested field.*not found"):
        controller.config.fields.get("net vlan /Common/vlan_external_az").fields.get(
            "customer-tag"
        )
