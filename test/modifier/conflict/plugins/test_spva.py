import pytest

config = """
security dos network-whitelist /Common/dos-network-whitelist {
    address-list /Common/addrList
}

sys compatibility-level {
    level 1
}

net address-list /Common/addrList {
    addresses {
        10.144.19.66 { }
        10.144.19.96 { }
        10.145.65.121 { }
    }
    description "This is a test address list whitelist"
}

security firewall address-list /Common/addrList {
    addresses {
        10.144.19.66 { }
        10.144.19.96 { }
        10.145.65.121 { }
    }
    description "This is a test address list whitelist"
}

security shared-objects address-list /Common/addrList {
    addresses {
        10.144.19.66 { }
        10.144.19.96 { }
        10.145.65.121 { }
    }
    description "This is a test address list whitelist"
}
"""

bigdb = """
[Dos.ForceSWdos]
default=false
type=enum
enum=|true|false|
realm=common
scf_config=true
display_name=Dos.ForceSWdos
value=false
"""


CONFLICT_NAME = "SPVA"


def test_spva_delete(test_solution):
    solution_name = "SPVA_delete_objects"

    controller = test_solution(
        conflict_name=CONFLICT_NAME,
        solution_name=solution_name,
        conf_file=config,
        conf_dat_file=bigdb,
    )

    with pytest.raises(KeyError, match=r"Requested key.*not found"):
        controller.config.fields.get(("security"))

    with pytest.raises(KeyError, match=r"Requested key.*not found"):
        controller.config.fields.get(("net"))

    node = controller.config.fields["sys compatibility-level"]
    assert node.fields["level"].value == "0"


def test_spdag_compatibility_lvl_1(test_solution):
    solution_name = "F5_Recommended_SPVA_compatibility_lvl_1"

    controller = test_solution(
        conflict_name=CONFLICT_NAME,
        solution_name=solution_name,
        conf_file=config,
        conf_dat_file=bigdb,
    )

    node = controller.config.fields["sys compatibility-level"]
    assert node.fields["level"].value == "1"
    assert (
        controller.config.bigdb.get(section="Dos.ForceSWdos", option="value") == "true"
    )
