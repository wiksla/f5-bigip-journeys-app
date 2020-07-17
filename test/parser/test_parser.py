from .configs import parse_config


def test_config_has_comments():
    payload = parse_config(config_file="with_comments/simple_comments.conf")
    assert payload == {
        "status": "ok",
        "errors": [],
        "config": [
            {
                "file": "unnamed",
                "status": "ok",
                "errors": [],
                "parsed": [
                    {
                        "line": 1,
                        "args": ["#"],
                        "comment": " Very important config note",
                    },
                    {
                        "line": 2,
                        "args": [
                            "ltm",
                            "virtual",
                            "/Common/EXPLICIT-PROXY-HTTPS-BYPASS",
                        ],
                        "block": [
                            {"line": 3, "args": ["destination", "/Common/0.0.0.0:443"]},
                            {
                                "line": 4,
                                "args": ["profiles"],
                                "block": [
                                    {"line": 5, "args": ["/Common/tcp"], "block": []}
                                ],
                            },
                            {"line": 7, "args": ["translate-address", "disabled"]},
                            {
                                "line": 8,
                                "args": ["#"],
                                "comment": " very important internal note",
                            },
                            {
                                "line": 9,
                                "args": ["vlans"],
                                "block": [
                                    {"line": 10, "args": ["/Common/tcp-forward-tunnel"]}
                                ],
                            },
                            {"line": 12, "args": ["vlans-enabled"]},
                        ],
                    },
                ],
            }
        ],
    }


def test_single_simple_object_single_quoted_prop():
    payload = parse_config("basic/single_simple_object_single_quoted_prop.conf")
    assert payload == {
        "status": "ok",
        "errors": [],
        "config": [
            {
                "file": "unnamed",
                "status": "ok",
                "errors": [],
                "parsed": [
                    {
                        "line": 1,
                        "args": ["cm", "device", "/Common/dev.dev"],
                        "block": [{"line": 2, "args": ["quoted", 'my " string']}],
                    }
                ],
            }
        ],
    }


def test_single_object_no_props():
    payload = parse_config("basic/single_simple_object_no_props.conf")
    assert payload == {
        "status": "ok",
        "errors": [],
        "config": [
            {
                "file": "unnamed",
                "status": "ok",
                "errors": [],
                "parsed": [
                    {
                        "line": 1,
                        "args": ["cm", "device", "/Common/dev.dev"],
                        "block": [],
                    }
                ],
            }
        ],
    }


def test_single_obj_single_empty_prop():
    payload = parse_config("basic/single_obj_single_empty_prop.conf")
    assert payload == {
        "status": "ok",
        "errors": [],
        "config": [
            {
                "file": "unnamed",
                "status": "ok",
                "errors": [],
                "parsed": [
                    {
                        "line": 1,
                        "args": ["cm", "device", "/Common/dev.dev"],
                        "block": [{"line": 2, "args": ["base-mac"], "block": []}],
                    }
                ],
            }
        ],
    }


def test_single_obj_flag():
    payload = parse_config("basic/single_obj_single_flag.conf")
    assert payload == {
        "status": "ok",
        "errors": [],
        "config": [
            {
                "file": "unnamed",
                "status": "ok",
                "errors": [],
                "parsed": [
                    {
                        "line": 1,
                        "args": ["cm", "device", "/Common/dev.dev"],
                        "block": [{"line": 2, "args": ["flag"]}],
                    }
                ],
            }
        ],
    }


def test_single_obj_flags_and_props():
    payload = parse_config("basic/single_obj_flags_and_props.conf")
    assert payload == {
        "status": "ok",
        "errors": [],
        "config": [
            {
                "file": "unnamed",
                "status": "ok",
                "errors": [],
                "parsed": [
                    {
                        "line": 1,
                        "args": ["cm", "device", "/Common/dev.dev"],
                        "block": [
                            {"line": 2, "args": ["flag1"]},
                            {"line": 3, "args": ["prop1", "val1"]},
                            {"line": 4, "args": ["flag2"]},
                            {"line": 5, "args": ["prop2", "val2"]},
                            {"line": 6, "args": ["prop3", "val3"]},
                        ],
                    }
                ],
            }
        ],
    }


def test_single_obj_nests():
    payload = parse_config("basic/single_obj_nests.conf")
    assert payload == {
        "status": "ok",
        "errors": [],
        "config": [
            {
                "file": "unnamed",
                "status": "ok",
                "errors": [],
                "parsed": [
                    {
                        "line": 1,
                        "args": ["ltm", "virtual", "/Common/APM-1-test_VS"],
                        "block": [
                            {
                                "line": 2,
                                "args": ["profiles"],
                                "block": [
                                    {
                                        "line": 3,
                                        "args": ["/Common/APM_connectivity_profile"],
                                        "block": [
                                            {
                                                "line": 4,
                                                "args": ["context", "clientside"],
                                            }
                                        ],
                                    },
                                    {
                                        "line": 6,
                                        "args": ["/Common/scconnect-clientssl"],
                                        "block": [
                                            {
                                                "line": 7,
                                                "args": ["context", "clientside"],
                                            }
                                        ],
                                    },
                                    {
                                        "line": 9,
                                        "args": [
                                            "/Common/serverssl-insecure-compatible"
                                        ],
                                        "block": [
                                            {
                                                "line": 10,
                                                "args": ["context", "serverside"],
                                            }
                                        ],
                                    },
                                ],
                            }
                        ],
                    }
                ],
            }
        ],
    }


def test_single_obj_double_nest():
    payload = parse_config("basic/single_obj_double_nest.conf")
    assert payload == {
        "status": "ok",
        "errors": [],
        "config": [
            {
                "file": "unnamed",
                "status": "ok",
                "errors": [],
                "parsed": [
                    {
                        "line": 1,
                        "args": ["ltm", "virtual", "/Common/APM-1-test_VS"],
                        "block": [
                            {
                                "line": 2,
                                "args": ["profiles"],
                                "block": [
                                    {
                                        "line": 3,
                                        "args": ["/Common/APM_connectivity_profile"],
                                        "block": [
                                            {
                                                "line": 4,
                                                "args": ["context", "clientside"],
                                            }
                                        ],
                                    }
                                ],
                            }
                        ],
                    }
                ],
            }
        ],
    }


def test_complex_obj():
    payload = parse_config("basic/complex_obj.conf")
    assert payload == {
        "status": "ok",
        "errors": [],
        "config": [
            {
                "file": "unnamed",
                "status": "ok",
                "errors": [],
                "parsed": [
                    {
                        "line": 1,
                        "args": ["ltm", "virtual", "/Common/APM-2-test_VS"],
                        "block": [
                            {
                                "line": 2,
                                "args": ["destination", "/Common/172.16.1.15:10443"],
                            },
                            {"line": 3, "args": ["ip-protocol", "tcp"]},
                            {"line": 4, "args": ["mask", "255.255.255.255"]},
                            {
                                "line": 5,
                                "args": ["profiles"],
                                "block": [
                                    {
                                        "line": 6,
                                        "args": ["/Common/APM-2_access_profile"],
                                        "block": [],
                                    },
                                    {
                                        "line": 7,
                                        "args": ["/Common/APM_connectivity_profile"],
                                        "block": [
                                            {
                                                "line": 8,
                                                "args": ["context", "clientside"],
                                            }
                                        ],
                                    },
                                    {
                                        "line": 10,
                                        "args": ["/Common/APM_rewrite_profile"],
                                        "block": [],
                                    },
                                    {"line": 11, "args": ["/Common/http"], "block": []},
                                    {"line": 12, "args": ["/Common/ppp"], "block": []},
                                    {"line": 13, "args": ["/Common/rba"], "block": []},
                                    {
                                        "line": 14,
                                        "args": ["/Common/scconnect-clientssl"],
                                        "block": [
                                            {
                                                "line": 15,
                                                "args": ["context", "clientside"],
                                            }
                                        ],
                                    },
                                    {
                                        "line": 17,
                                        "args": [
                                            "/Common/serverssl-insecure-compatible"
                                        ],
                                        "block": [
                                            {
                                                "line": 18,
                                                "args": ["context", "serverside"],
                                            }
                                        ],
                                    },
                                    {"line": 20, "args": ["/Common/tcp"], "block": []},
                                    {
                                        "line": 21,
                                        "args": ["/Common/websso"],
                                        "block": [],
                                    },
                                ],
                            },
                            {
                                "line": 23,
                                "args": ["rules"],
                                "block": [{"line": 24, "args": ["/Common/APM_iRule"]}],
                            },
                            {"line": 26, "args": ["source", "0.0.0.0/0"]},
                            {
                                "line": 27,
                                "args": ["source-address-translation"],
                                "block": [{"line": 28, "args": ["type", "automap"]}],
                            },
                            {"line": 30, "args": ["translate-address", "enabled"]},
                            {"line": 31, "args": ["translate-port", "enabled"]},
                            {
                                "line": 32,
                                "args": ["vlans"],
                                "block": [{"line": 33, "args": ["/Common/vnmet1"]}],
                            },
                            {"line": 35, "args": ["vlans-enabled"]},
                        ],
                    }
                ],
            }
        ],
    }
