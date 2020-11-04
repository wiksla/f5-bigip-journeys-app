import json
import random
from collections import OrderedDict
from copy import deepcopy
from itertools import cycle
from pathlib import Path
from string import ascii_letters
from typing import Dict


def make_html_file(filename, html):
    with open(filename, "w") as f:
        f.write(html)


def make_mock_header(title):
    return {
        "title": title,
        "migration_start_time": "2020-10-22T12:27:59Z",
        "source": {
            "ucs": {
                "filename": "ucs_filename.ucs",
                "version": "14.1.2.8-0.0.433 (bigip14.1.x-miro)",
                "platform": "C118",
            },
            "as3": {"filename": "as3_filename.json"},
        },
    }


def make_mock_obj_list():
    return [
        "ltm pool /Common/test-iapp-1.app/test-iapp-1_pool {",
        "    app-service /Common/test-iapp-1.app/test-iapp-1",
        "    load-balancing-mode least-connections-member",
        "    members {",
        "        /Common/6.6.7.7:80 {",
        "            address 6.6.7.7",
        "            app-service /Common/test-iapp-1.app/test-iapp-1",
        "        }",
        "    }",
        "    monitor /Common/test-iapp-1.app/test-iapp-1_http_monitor",
        "    slow-ramp-time 300",
        "}",
    ]


def make_mock_affected_obj_item(id):
    # TODO: add error handler (id arg)
    id_str = str(id)
    obj_list = make_mock_obj_list()

    affected_obj_item = dict(
        file="some-file-name-" + id_str,
        comment="some-comment-" + id_str,
        object=obj_list,
    )
    return affected_obj_item


def make_mock_affected_obj_dict(size):
    # TODO: error handler (size arg)
    prefix = "affected_obj_"
    suffix = "_key"
    affected_obj_dict = dict()

    for x in range(size):
        affected_obj_key = prefix + str(x) + suffix
        affected_obj_item = make_mock_affected_obj_item(x)
        affected_obj_dict[affected_obj_key] = affected_obj_item

    return affected_obj_dict


def make_mock_conflict_item(id, size):
    # TODO: error handler (id, size args)
    id_str = str(id)
    conflict_id = "conflict-" + id_str + "-id-SPDAG"
    conflict_summary = (
        "conflict-"
        + id_str
        + "-summary- net vlan /Common/vlan1: Value of field cmp hash is not supported on target platform"
    )
    affected_objects = make_mock_affected_obj_dict(size)
    conflict_item = dict(
        id=conflict_id, summary=conflict_summary, affected_objects=affected_objects
    )
    return conflict_item


def make_mock_conflicts_list(list_size, conflict_size):
    # TODO: error handler (list_size, conflict_size args)
    mock_conflicts_list = list()
    for x in range(list_size):
        mock_conflict_item = make_mock_conflict_item(x, conflict_size)
        mock_conflicts_list.append(mock_conflict_item)
    return mock_conflicts_list


def make_mock_conflicts_json_data(response_size, conflict_size):
    # TODO: error handler (response_size, conflict_size args)
    mock_conflicts_list_dict = make_mock_conflicts_list(response_size, conflict_size)
    mock_conflicts_list_json = json.dumps(mock_conflicts_list_dict, indent=4)
    return mock_conflicts_list_json


def get_mock_validation_data(scaling, filename: str = ""):
    raw_data = get_raw_mock_validation_data(filename)
    scaled_data = scale_mock_validation_data(raw_data, scaling)
    return scaled_data


def get_raw_mock_validation_data(filename: str):
    if not filename:
        filename = str(Path("validators_results_example.json"))
        # Path is OS friendly, returns POSIX and Windows styled paths.
    with open(filename) as f:
        raw_data = json.load(f)
    return raw_data


def scale_mock_validation_data(data: Dict, value_sizes=None):
    if value_sizes is None:
        return data

    scaled_data = deepcopy(data)
    try:
        for validator, results_size in value_sizes.items():
            value_keys = data[validator]["value"].keys()
            if value_keys:
                values = cycle(value_keys)
            else:
                continue
            scaled_data[validator]["value"] = {}  # reset number of logs
            for _ in range(value_sizes[validator]):
                current_val = next(values)
                if current_val in scaled_data[validator]["value"].keys():
                    scaled_data[validator]["value"][
                        f"{current_val}_{get_random_str()}"
                    ] = data[validator]["value"][current_val]
                else:
                    scaled_data[validator]["value"][current_val] = data[validator][
                        "value"
                    ][current_val]
    except AttributeError:
        raise Exception(
            f"error i data of: {validator}, data[validator]['value']: {data[validator]['value']}"
        )
    except KeyError:
        raise Exception(f"error i data of: {validator}")
    return scaled_data


def get_random_str(length: int = 8) -> str:
    return "".join([random.choice(ascii_letters) for _ in range(length)])


#
# """ uncomment in case of troubles."""
#
# def get_raw_mock_validation_data(filename):  Filename is dummy arg
#     data = {
#         "MCP status": {
#             "result": "PASSED",
#             "value": {
#                 "end-platform-id-received": "true",
#                 "last-load": "full-config-load-succeed",
#                 "phase": "running",
#             },
#         },
#         "TMM status": {
#             "result": "FOR_USER_EVALUATION",
#             "value": {
#                 "five-sec-avg-usage-ratio": "1",
#                 "one-min-avg-usage-ratio": "1",
#                 "memory-total": "13.5G",
#                 "npus": "4",
#                 "memory-used": "407.3M",
#                 "five-min-avg-usage-ratio": "1",
#             },
#         },
#         "Prompt state": {
#             "result": "PASSED",
#             "value": {"info": "prompt isn't nasty!! "},
#         },
#         "Core dumps": {"result": "PASSED", "value": {"info": "No core dumps detected"}},
#         "DB compare": {
#             "result": "FOR_USER_EVALUATION",
#             "value": {"info": "we don't have your data"},
#         },
#         "Memory footprint": {"result": "FOR_USER_EVALUATION", "value": {}},
#         "Version check": {"result": "FOR_USER_EVALUATION", "value": {}},
#         "LTM VS check": {
#             "result": "FOR_USER_EVALUATION",
#             "value": {
#                 "my_vs_1": {
#                     "status.availabilityState": {"description": "unknown"},
#                     "status.enabledState": {"description": "enabled"},
#                     "status.statusReason": {
#                         "description": "The children pool member(s) either don\u0027t "
#                         "have service checking enabled, or service "
#                         "check results are not available yet"
#                     },
#                 }
#             },
#         },
#     }
#     return data


def get_mock_deployment_data(validation_results_path: str = ""):
    # some info about expected data:
    scaled_sizes = OrderedDict()
    scaled_sizes["MCP status"] = 6  # len will be 6 in 99% cases
    scaled_sizes["TMM status"] = 6  # len will be 6 in 99% cases
    scaled_sizes["Prompt state"] = 1  # len will be 1
    scaled_sizes["Core dumps"] = 1  # len will be 1
    scaled_sizes["DB compare"] = 5  # len can vary from 10 to dozens of 100
    scaled_sizes["Memory footprint"] = 10  # len can vary betw 5-50
    scaled_sizes["Version check"] = 1  # this is 1
    scaled_sizes["LTM VS check"] = 10  # can be from 1 to 100.000

    return {
        "config_name": "my_precious_migrated_ucs.ucs",
        "destination_ip": "10.145.1.12",
        "config_loading_result": "SUCCESS",
        "loading_duration": "5m23s",
        "validation": get_mock_validation_data(scaled_sizes, validation_results_path),
    }


single_mock_add_change = [
    "apm report default-report {",
    "    report-name sessionReports/sessionSummary",
    "    user /Common/admin",
    "}",
]


single_mock_remove_change = [
    "ltm pool /Common/pcf-gorouter1-mdc-pc1_9060 {",
    "    load-balancing-mode least-connections-member",
    "    members {",
    "        /Common/10.175.24.22:80 {",
    "            address 10.175.24.22",
    "        }",
    "    }",
    "    monitor /Common/rubicon-sso-prod-mdc-pcf",
    "}",
]


def make_mock_insert_change(change_size):

    return {
        "change_type": "insert",
        "previous_text": [],
        "current_text": change_size * single_mock_add_change,
        "previous_line": 21,
        "current_line": 21,
    }


def make_mock_replacement_change(change_size):
    return {
        "change_type": "replace",
        "previous_text": change_size * single_mock_remove_change,
        "current_text": change_size * single_mock_add_change,
        "previous_line": 121,
        "current_line": 161,
    }


def make_mock_delete_change(change_size):
    return {
        "change_type": "delete",
        "previous_text": change_size * single_mock_remove_change,
        "current_text": [],
        "previous_line": 221,
        "current_line": 281,
    }


def make_mock_file_resolutions(change_size):
    return [
        make_mock_insert_change(change_size),
        make_mock_replacement_change(change_size),
        make_mock_delete_change(change_size),
    ]


def make_mock_resolution(id, change_size):
    id_str = str(id)
    return {
        "message": "CONFLICT_" + id_str + "_RESOLUTION",
        "diffs": {
            f"file_{i}": make_mock_file_resolutions(change_size)
            for i in range(change_size)
        },
    }


def make_mock_resolutions_list(response_size, change_size):
    return [make_mock_resolution(i, change_size) for i in range(response_size)]


def make_conflicts_report_obj(list_size, conflict_size):
    return {
        "header": make_mock_header("Conflicts report"),
        "conflicts": make_mock_conflicts_list(list_size, conflict_size),
    }


def make_resolutions_report_obj(list_size, conflict_size):
    return {
        "header": make_mock_header("Resolutions report"),
        "conflicts": make_mock_conflicts_list(list_size, conflict_size),
        "resolutions": make_mock_resolutions_list(list_size, conflict_size),
    }


def make_deployment_validation_report_obj(
    list_size,
    conflict_size,
    validation_results_path: str = "",
    custom_validation_results_sizes=None,
):
    """Make data obj with mocked data for overall report including:
    conflicts, resolutions, deployment & validation result

    :param list_size:
    :param conflict_size:
    :param validation_results_path: path to json file with results (i.e. from tests)
    :param custom_validation_results_sizes: Dictionary with validators' names as keys
    and unsigned integers as values. Number indicates "value" dict size inside
    validator's result.

    Each validator result has following structure:

        "<validator_name>": {
            "result": "<result>",
            "value": {
                "<key1>": <data>,
                "key2": {"can": "be",
                         "nested": {"like": "that!"},
                },
            },

    giving any number method will produce value dict of that size for testing purposes
    of HTML formatting. Provide own dict (ordered or not) or change numbers below.
    Comment
    :return: A dictionary all data you may need (for now)
    """

    return {
        "header": make_mock_header("Journey report"),
        "conflicts": make_mock_conflicts_list(list_size, conflict_size),
        "resolutions": make_mock_resolutions_list(list_size, conflict_size),
        "deployment": get_mock_deployment_data(),
    }
