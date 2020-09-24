import pytest

config = """
ltm virtual /Common/pem_http_virt {
    destination /Common/0.0.0.0:80
    ip-protocol tcp
    mask any
    profiles {
        /Common/PEM_Steering_pem_profile {
            context clientside
        }
        /Common/classification {
            context clientside
        }
        /Common/fastL4 { }
    }
    source 0.0.0.0/0
    translate-address enabled
    translate-port enabled
}

pem forwarding-endpoint /Common/endpoint1 {
    description "Forward traffic to <pool1> members"
    pool /Common/pool1
    translate-address enabled
}

pem forwarding-endpoint /Common/endpoint2 {
    description "Forward traffic to <pool2> members"
    pool /Common/pool2
    translate-address enabled
}

pem policy /Common/drop {
    rules {
        rule1 {
            flow-info-filters {
                filter0 { }
            }
            gate-status disabled
            precedence 100
        }
    }
}

pem policy /Common/policy_1_to_2 {
    description "Forward 10.40.0.x to 10.255.1.1"
    rules {
        forward_rule1 {
            flow-info-filters {
                filter0 {
                    dst-ip-addr 10.255.0.1/32
                    dst-port 80
                    ip-addr-type IPv4
                    proto tcp
                    src-ip-addr 10.40.0.0/24
                }
            }
            forwarding {
                endpoint /Common/endpoint2
                type pool
            }
            precedence 1
        }
    }
}

pem subscriber /Common/1user1 {
    ip-address-list { 10.40.0.1 }
    policies {
        /Common/policy_1_to_2
    }
    subscriber-id-type private
}

pem global-settings analytics { }

pem profile spm /Common/PEM_Steering_pem_profile {
    app-service none
    description "Created by Web Configuration Utility for PEM Listener PEM_Steering"
    fast-pem enabled
    fast-vs-name /Common/pem_http_virt
    global-policies-high-precedence {
        /Common/policy_1_to_2
    }
    unknown-subscriber-policies {
        /Common/drop
    }
}

pem profile spm /Common/spm {
    app-service none
}

sys provision pem {
    level nominal
}

ltm rule /Common/tcp-proxy-header-irule {
    when PEM_POLICY {
        set ip [IP::client_addr]
        log local0. "------- Matched PEM Policy [PEM::policy name] ---------"
        log local0. "Changing Subscriber ID and type with command PEM::session info $ip subscriber 10.10.10.10 nai"
        PEM::session info $ip subscriber "10.10.10.10" "nai"
        log local0. "Subscriber Type [PEM::session info [IP::client_addr] subscriber-type]"
        log local0. "Subscriber ID [PEM::session info [IP::client_addr] subscriber-id]"
        log local0. "----------------------------------------------------"
    }
}
"""


CONFLICT_NAME = "PEM"


def test_pem_modify(test_solution):
    solution_name = "F5_Recommended_PEM_adjust_objects"

    controller = test_solution(
        conflict_name=CONFLICT_NAME, solution_name=solution_name, conf_file=config,
    )

    node = controller.config.fields["sys provision pem"]
    assert node.fields["level"].value == "none"

    with pytest.raises(KeyError, match=r"Requested key.*not found"):
        controller.config.fields.get(("pem"))

    with pytest.raises(KeyError, match=r"Requested field.*not found"):
        controller.config.fields.get(("ltm", "virtual")).fields["profiles"].fields[
            "/Common/PEM_Steering_pem_profile"
        ]

    obj_irule = controller.config.fields.get(2)
    assert obj_irule.data["comment"]
