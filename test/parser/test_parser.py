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
                        "block": [{"line": 2, "args": ["quoted", "my string"]}],
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


def test_iapp_nested_blob_nasty_escape():
    payload = parse_config("messy/iapp_nested_blob_nasty_escape.conf")
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
                        "args": ["cli", "script", "/Common/f5.iapp.1.1.1.cli"],
                        "block": [
                            {
                                "line": 1,
                                "args": [
                                    '\nproc iapp_make_safe_password { password } {\n    return [string map { \\\' \\\\\\\\\\\\\\\' \\# \\\\\\\\\\\\\\# \\\\ \\\\\\\\\\\\\\\\ } $password]\n}\nproc iapp_get_items { args } {\n\n    # Set default values.\n    set error_msg  "iapp_get_items $args:"\n    set do_binary  0\n    set nocomplain 0\n    set items      ""\n    set join_char  "\\n"\n    set recursive  "recursive"\n    set com_dir    "/Common"\n    set loc_dir    "[tmsh::pwd]"\n\n    # Set up flag-related work.\n    array set flags  {\n        -exists      { [set do_binary 1] }\n        -nocomplain  { [set nocomplain 1] }\n        -list        { [set join_char " "] }\n        -norecursive { [set recursive ""] }\n        -local       { [set com_dir   ""] }\n        -dir         { [set loc_dir      [iapp_pull $ptr args]] }\n        -filter      { [set filter_field [iapp_pull $ptr args]] \\\n                       [set filter_op    [iapp_pull $ptr args]] \\\n                       [set filter_value [iapp_pull $ptr args]] }\n    }\n    iapp_process_flags flags args\n}\n'
                                ],
                            }
                        ],
                    }
                ],
            }
        ],
    }


def test_nested_blob_not_comment():
    payload = parse_config("messy/cli_script.conf")
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
                        "args": ["cli", "script", "/Common/f5.iapp.1.1.3.cli"],
                        "block": [
                            {
                                "line": 1,
                                "args": [
                                    '\n#  Initialization proc for all templates.\n#  Parameters "start" and "stop" or "end".\nproc iapp_upgrade_template { upgrade_var upgrade_trans } {\n    upvar $upgrade_var   upgrade_var_arr\n    upvar $upgrade_trans upgrade_trans_arr\n\n    # create the new variables from the old\n    foreach { var } [array names upgrade_var_arr] {\n\n        # substitute old variable name for abbreviation "##"\n        regsub -all {##} $upgrade_var_arr($var) \\$$var map_cmd\n\n        # run the mapping command from inside the array\n        if { [catch { subst $map_cmd } err] } {\n            if { [string first "no such variable" $err] == -1 } {\n                puts "ERROR $err"\n            }\n        }\n    }\n}\n'
                                ],
                            }
                        ],
                    }
                ],
            }
        ],
    }


def test_nested_blob_nasty_escapes():
    payload = parse_config("messy/nested_blob_nasty_escapes.conf")
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
                        "args": ["cli", "script", "/Common/f5.iapp.1.1.3.cli"],
                        "block": [
                            {
                                "line": 1,
                                "args": [
                                    "\nproc iapp_make_safe_password { password } {\n    return [string map { \\' \\\\\\' \\\" \\\\\\\" \\{ \\\\\\{ \\} \\\\\\} \\; \\\\\\; \\| \\\\\\| \\# \\\\\\# \\  \\\\\\  \\\\ \\\\\\\\ } $password]\n}\n"
                                ],
                            }
                        ],
                    }
                ],
            }
        ],
    }


def test_ltm_rule_commented_when():
    payload = parse_config("messy/ltm_rule_commented_when.conf")
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
                        "args": ["ltm", "rule", "/Common/DEECD_BLOCKSYMANTEC"],
                        "block": [
                            {
                                "line": 1,
                                "args": [
                                    '\n                                            #when HTTP_REQUEST {\n#if { [[string tolower [HTTP::host]] contains "ent-shasta-rrs.symantec.com"] }\n#{\n#HTTP::close\n#}\n#}\n\nwhen HTTP_REQUEST {\n    if { [HTTP::host] contains "ent-shasta-rrs.symantec.com"} {\n        #log local0. "Closing Symantec connection [IP::client_addr]:[TCP::client_port] -> [\n        IP::local_addr]:[TCP::local_port]"\n        HTTP::close\n    }\n}\n'
                                ],
                            }
                        ],
                    }
                ],
            }
        ],
    }


def test_ltm_rule_commented_when_2():
    payload = parse_config("messy/ltm_rule_commented_when2.conf")
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
                        "args": ["ltm", "rule", "/Common/iRule_campbells_AWS_80_v2.0"],
                        "block": [
                            {
                                "line": 1,
                                "args": [
                                    '\n    when CLIENT_ACCEPTED {\n\tset IP::addr [getfield [IP::client_addr] "%" 1]\n        set retries 0\n}\n\nwhen HTTP_REQUEST {\n    if {not[class match [IP::client_addr] equals NETSTART_Allowed_IP]} {\n           reject\n    }\n   \tif {$static::debug} {log local0. "campbells_AWS_80- The URI was <[HTTP::uri]> "}\n\n\tswitch -glob [HTTP::uri] {\n\t\t"/convenience/login*" -\n\t\t"/convenience/register*" {\n    \t\t  if {$static::debug} {log local0. "campbells_AWS_80- The URI was <[HTTP::uri]>\n    \t\t  Redirect to HTTPS " }\n  \t\t# pool Pool_AWSUS_hybris_b2b-prd-app_80\n              HTTP::redirect https://[getfield [HTTP::host] ":" 1][HTTP::uri]\n               # HTTP::respond 302 Location "https://[HTTP::host][HTTP::uri]"\n\n\t\t}\n   \t\t"/images/*" -\n  \t\t"/_ui/*" -\n    \t\t"/favicon.ico*" -\n   \t\t"/convenience*" -\n   \t\t"/medias/*"  {\n                        pool Pool_AWSUS_hybris_b2b-prd-app_80\n   \t\t\tif {$static::debug} {log local0. "campbells_AWS_80- The URI was <[HTTP::uri]> -\n   \t\t\tAllowed client <$IP::addr> is now connecting to pool\n   \t\t\t<Pool_AWSUS_hybris_b2b-prd-app_80>" }\n   \t\t}\n\t\t"/ccc/*"  {\n\t\t\t#HTTP::redirect https://[HTTP::host][HTTP::uri]\n                       pool Pool_ccc_landingpage_metwebdev09\n\t\t\tif {$static::debug} {log local0. "campbells_AWS_80- The URI was <[HTTP::uri]> -\n\t\t\tAllowed client <$IP::addr> is now connecting to pool <Pool_ccc_landingpage>" }\n\t\t}\n                "/iga/*" {\n\t\t         HTTP::respond 302 Location "https://[HTTP::host][HTTP::uri]"\n                }\n\t\tdefault {\n\n\n                          pool Pool_campbells_125\n\n           \t\tif {$static::debug} {log local0. "campbells_AWS_80- The URI was <[HTTP::uri]> -\n           \t\tAllowed client <$IP::addr> is now connecting to pool\n           \t\t<Pool_AWSUS_hybris_b2b-prd-app_80>" }\n   \t\t}\n\n    }\n}\n\n#when HTTP_RESPONSE {\n# HTTP::header replace X-Frame-Options "SAMEORIGIN"\n'
                                ],
                            }
                        ],
                    }
                ],
            }
        ],
    }
