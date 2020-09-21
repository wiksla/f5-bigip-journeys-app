import pytest

config = """
net stp /Common/cist {
    trunks {
        trunk0 {
            external-path-cost 200
            internal-path-cost 200
        }
    }
    vlans {
        /Common/external
        /Common/internal
    }
}

net trunk trunk0 {
    interfaces {
        1/1.0
        1/2.0
    }
}

net vlan /Common/external {
    interfaces {
        trunk0 {
            tag-mode service
            tagged
        }
    }
    tag 1128
}

net vlan /Common/internal {
    interfaces {
        trunk0 {
            tag-mode service
            tagged
        }
    }
    tag 1135
}
"""


CONFLICT_NAME = "TRUNK"


def test_trunk_delete(test_solution):
    solution_name = "F5_Recommended_TRUNK_delete_objects"

    controller = test_solution(
        conflict_name=CONFLICT_NAME, solution_name=solution_name, conf_file=config,
    )

    with pytest.raises(KeyError, match=r"Requested key.*not found"):
        controller.config.fields.get("net trunk trunk0")

    with pytest.raises(KeyError, match=r"Requested field.*not found"):
        controller.config.fields.get(("net", "stp")).fields["trunks"]

    with pytest.raises(KeyError, match=r"Requested field.*not found"):
        controller.config.fields.get("net vlan /Common/internal").fields["interfaces"]
