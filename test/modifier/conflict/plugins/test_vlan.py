import pytest

config = """
net vlan-group /Common/vlanGroup_AZ {
    description "This is an example of VLAN Group"
    members {
        /Common/vlan_external_az
        /Common/vlan_internal_az
    }
}

net route-domain /Common/0 {
    id 0
    vlans {
        /Common/vlan_internal_az
        /Common/vlan_external_az
        /Common/socks-tunnel
        /Common/http-tunnel
        /Common/vlanGroup_AZ
    }
}
"""


CONFLICT_NAME = "VlanGroup"


def test_vlan_group_resolution_delete(test_solution):
    solution_name = "F5_Recommended_VlanGroup_delete_objects"

    controller = test_solution(
        conflict_name=CONFLICT_NAME, solution_name=solution_name, conf_file=config,
    )

    with pytest.raises(KeyError, match=r"Requested key.*not found"):
        controller.config.fields.get(("net", "vlan-group"))

    with pytest.raises(KeyError, match=r"Requested key.*not found"):
        controller.config.fields.get(("net", "route-domain")).fields[
            "vlans"
        ].fields.get("/Common/vlanGroup_AZ")
