import pytest

config = """
security dos network-whitelist /Common/dos-network-whitelist {
    extended-entries {
        testWhitelist {
            description "This is a test wildcard whitelist"
        }
    }
}

sys compatibility-level {
    level 2
}
"""


CONFLICT_NAME = "WildcardWhitelist"


def test_wildcard_whitelist_adjust(test_solution):
    solution_name = "F5_Recommended_WildcardWhitelist_adjust_objects"

    controller = test_solution(
        conflict_name=CONFLICT_NAME, solution_name=solution_name, conf_file=config,
    )

    node = controller.config.fields["sys compatibility-level"]
    assert node.fields["level"].value == "0"

    with pytest.raises(KeyError, match=r"Requested key.*not found"):
        controller.config.fields.get(
            "security dos network-whitelist /Common/dos-network-whitelist"
        )
