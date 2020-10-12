import pytest

config = """
sys feature-module cgnat {
    enabled
}

ltm lsn-pool /Common/lsn_pool {
    egress-interfaces {
        /Common/vlan1
    }
    egress-interfaces-enabled
    mode deterministic
}

ltm lsn-pool /Common/test_pool_cgnat_lsn {
     egress-interfaces {
        /Common/vlan1
    }
    egress-interfaces-enabled
}

ltm profile pcp /Common/test_cgnat_profile {
    announce-after-failover disabled
    announce-multicast 10
    app-service none
    defaults-from /Common/pcp
    map-filter-limit 1
    map-limit-per-client 65535
    map-recycle-delay 60
    max-mapping-lifetime 86400
    min-mapping-lifetime 600
    rule /Common/_sys_APM_Office365_SAML_BasicAuth
    third-party-option disabled
}

ltm virtual /Common/VS_cgnat {
    creation-time 2020-05-08:01:14:53
    destination /Common/10.146.141.131:0
    ip-protocol tcp
    last-modified-time 2020-05-08:01:14:53
    mask 255.255.255.255
    profiles {
        /Common/tcp { }
   }
    source 0.0.0.0/24
    source-address-translation {
        pool /Common/test_pool_cgnat_lsn
        type lsn
    }
    translate-address disabled
    translate-port disabled
}

ltm profile pcp /Common/test_ltm_profile_pcp {
    app-service none
    defaults-from /Common/pcp
}

ltm profile map-t /Common/test_ltm_profile_mapt {
    app-service none
    defaults-from /Common/mapt
    description ""Profile created in LTM section""
}
"""


CONFLICT_NAME = "CGNAT"


def test_cgnat_delete(test_solution):
    solution_name = "F5_Recommended_CGNAT_delete_objects"

    controller = test_solution(
        conflict_name=CONFLICT_NAME, solution_name=solution_name, conf_file=config,
    )

    with pytest.raises(KeyError, match=r"Requested key.*not found"):
        controller.config.fields.get(("ltm", "lsn-pool"))
        controller.config.fields.get(("ltm", "profile", "pcp"))
        controller.config.fields.get(("ltm", "virtual"))
        controller.config.fields.get(("ltm", "profile", "map-t"))
