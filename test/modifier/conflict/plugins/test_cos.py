import pytest

config = """
net cos global-settings {
    default-map-dscp { /Common/map_GOLD /Common/map_SILVER /Common/map_BRONZE }
    default-traffic-priority /Common/DEFAULT_PRIORITY
    precedence dscp-only
    feature-enabled
}
net cos map-dscp /Common/map_BRONZE {
    traffic-priority /Common/BRONZE
    value 24
}
net cos map-dscp /Common/map_GOLD {
    traffic-priority /Common/GOLD
    value 40
}
net cos map-dscp /Common/map_SILVER {
    traffic-priority /Common/SILVER
    value 56
}
net cos traffic-priority /Common/BRONZE {
    weight 1
}
net cos traffic-priority /Common/DEFAULT_PRIORITY {
    weight 5
}
net cos traffic-priority /Common/GOLD {
    weight 100
}
net cos traffic-priority /Common/SILVER {
    weight 10
}
"""


CONFLICT_NAME = "ClassOfService"


def test_cos_resolution_delete(test_solution):
    solution_name = "F5_Recommended_ClassOfService_delete_objects"

    controller = test_solution(
        conflict_name=CONFLICT_NAME, solution_name=solution_name, conf_file=config,
    )

    with pytest.raises(KeyError, match=r"Requested key.*not found"):
        controller.config.fields.get(("net", "cos"))
