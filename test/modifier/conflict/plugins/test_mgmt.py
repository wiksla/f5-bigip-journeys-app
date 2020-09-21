config = """
sys global-settings {
    gui-setup disabled
    mgmt-dhcp enabled
}
"""


CONFLICT_NAME = "MGMT-DHCP"


def test_mgmt_disable(test_solution):
    solution_name = "F5_Recommended_MGMT-DHCP_disable_mgmt_dhcp"

    controller = test_solution(
        conflict_name=CONFLICT_NAME, solution_name=solution_name, conf_file=config,
    )

    node = controller.config.fields["sys global-settings"]
    assert node.fields["mgmt-dhcp"].value == "disabled"
