import pytest

config = """
ltm virtual /Common/my_virtual_wire_vs {
    creation-time 2020-07-01:07:07:28
    destination /Common/10.0.0.0:0
    ip-protocol tcp
    l2-forward
    last-modified-time 2020-07-01:07:07:28
    mask 255.255.255.0
    profiles {
        /Common/fastL4 { }
    }
    source 0.0.0.0/0
    translate-address disabled
    translate-port disabled
    vlans {
        /Common/virtWire
    }
    vlans-enabled
}

net stp /Common/cist {
    trunks {
        trunk_external {
            external-path-cost 2000
            internal-path-cost 2000
        }
        trunk_internal {
            external-path-cost 2000
            internal-path-cost 2000
        }
    }
    vlans {
        /Common/virtWire_vlan_4096_1_353
        /Common/virtWire_vlan_4096_2_354
    }
}

net interface 1.1 {
    port-fwd-mode virtual-wire
}
net interface 2.1 {
    port-fwd-mode virtual-wire
}

net route-domain /Common/0 {
    id 0
    vlans {
        /Common/http-tunnel
        /Common/socks-tunnel
        /Common/virtWire_vlan_4096_2_354
        /Common/virtWire
        /Common/virtWire_vlan_4096_1_353
    }
}

net trunk trunk_external {
    interfaces {
        2.1
        2.2
    }
    lacp enabled
}
net trunk trunk_internal {
    interfaces {
        1.1
        1.2
    }
    lacp enabled
}

net vlan /Common/virtWire_vlan_4096_1_353 {
    interfaces {
        trunk_external {
            tag-mode service
            tagged
        }
    }
    tag 4096
}

net vlan /Common/virtWire_vlan_4096_2_354 {
    interfaces {
        trunk_internal {
            tag-mode service
            tagged
        }
    }
    tag 4096
}

net vlan-group /Common/virtWire {
    members {
        /Common/virtWire_vlan_4096_1_353
        /Common/virtWire_vlan_4096_2_354
    }
    mode virtual-wire
    vwire-propagate-linkstatus enabled
}

net fdb vlan /Common/virtWire_vlan_4096_1_353 { }
net fdb vlan /Common/virtWire_vlan_4096_2_354 { }
"""

CONFLICT_NAME = "VirtualWire"


def test_virtual_wire_resolution_delete(test_solution):
    solution_name = "F5_Recommended_VirtualWire_delete_objects"
    controller = test_solution(
        conflict_name=CONFLICT_NAME, solution_name=solution_name, conf_file=config,
    )

    with pytest.raises(KeyError, match=r"Requested key.*not found"):
        controller.config.fields.get(("net", "vlan-group"))

    node = controller.config.fields.get("net trunk trunk_internal").fields["interfaces"]
    assert node.value == ""
    node = controller.config.fields.get("net trunk trunk_external").fields["interfaces"]
    assert node.value == ""

    with pytest.raises(KeyError, match=r"Requested key.*not found"):
        controller.config.fields.get(("net", "interface"))

    node = controller.config.fields.get("net stp /Common/cist").fields["trunks"]
    assert node.value == ""

    with pytest.raises(KeyError, match=r"Requested key.*not found"):
        controller.config.fields.get("net vlan /Common/virtWire_vlan_4096_1_353")

    node = controller.config.fields.get("net route-domain /Common/0").fields["vlans"]
    assert "/Common/http-tunnel" in node.fields
    assert "/Common/virtWire_vlan_4096_2_354" not in node.fields
