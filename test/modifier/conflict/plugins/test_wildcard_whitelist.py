import pytest

config = """
security dos network-whitelist /Common/dos-network-whitelist {
    extended-entries {
        testWhitelist {
            description "This is a test wildcard whitelist"
        }
    }
}

"""


CONFLICT_NAME = "WildcardWhitelist"


def test_wildcard_whitelist_adjust(test_solution):
    solution_name = "F5_Recommended_WildcardWhitelist_delete_objects"

    controller = test_solution(
        conflict_name=CONFLICT_NAME, solution_name=solution_name, conf_file=config,
    )

    with pytest.raises(KeyError, match=r"Requested key.*not found"):
        controller.config.fields.get(
            "security dos network-whitelist /Common/dos-network-whitelist"
        )
