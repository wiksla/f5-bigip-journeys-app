from difflib import HtmlDiff
from difflib import unified_diff
from typing import Dict
from typing import List

from deepdiff import DeepDiff
from pyparsing import Word
from pyparsing import alphas
from pyparsing import nums

from journeys.utils.device import Device
from journeys.validators.ciphersuites_handler import get_ciphersuites_from_devices
from journeys.validators.cron_check import get_crontabs
from journeys.validators.exceptions import InputError


def tmsh_compare_as_html(cmd: str, first: Device, second: Device, **kwargs):
    """Test presenting diff of outputs of any tmsh command run on a BigIPs."""
    hd = HtmlDiff(**kwargs)
    diff = hd.make_file(
        *[
            device.ssh.run(cmd).stdout.splitlines(keepends=True)
            for device in (first, second)
        ]
    )
    return "".join(diff)


def convert_raw_to_dict(db_obj) -> dict:
    """Apply change operations to DB dict.
    - remove keys starting with `_`.
    - remove self links that always changes between versions.
    """
    ret_dict = {}
    for key, value in db_obj.items():
        if not key.startswith("_") and key != "selfLink":
            ret_dict[key] = value
    return ret_dict


def get_all_dbs_raw(device: Device) -> dict:
    """Return dict of modified Db objects."""
    collection = device.icontrol.mgmt.tm.sys.dbs.get_collection()
    raw_dbs = {item.name: convert_raw_to_dict(item.raw) for item in collection}
    return raw_dbs


def get_dbs_from_devices(first: Device, second: Device) -> list:
    """Get list of DBs from both devices."""
    return [get_all_dbs_raw(device) for device in (first, second)]


def compare_db(first: Device, second: Device):
    """Run DeepDiff against devices' DBs."""
    return DeepDiff(*get_dbs_from_devices(first, second))


def get_modules_footprint(device: Device) -> Dict:
    """Return dictionary of modules and their provisioned resources."""
    provisinon_lines = device.ssh.run("tmsh show sys provision").stdout.splitlines()[
        5:-1
    ]
    expr = Word(alphas) + Word(nums) * 4
    output_dict = dict()
    for line in provisinon_lines:
        parsed_output = expr.parseString(line)
        output_dict[parsed_output[0]] = {
            "cpu": {"value": int(parsed_output[1]), "unit": "%"},
            "memory": {"value": int(parsed_output[2]), "unit": "MB"},
            "host-memory": {"value": int(parsed_output[3]), "unit": "MB"},
            "disk": {"value": int(parsed_output[4]), "unit": "MB"},
        }
    return output_dict


def get_modules_footprint_from_devices(first: Device, second: Device) -> List:
    """Return modules footprint for both devices."""
    return [get_modules_footprint(device) for device in (first, second)]


def compare_memory_footprint(first: Device, second: Device):
    """Run DeepDiff against devices' memory footprint output."""
    return DeepDiff(*get_modules_footprint_from_devices(first, second))


def compare_ciphersuites(first: Device, second: Device) -> DeepDiff:
    """Run DeepDiff against devices' available ciphersuites."""
    return DeepDiff(*get_ciphersuites_from_devices(first, second))


def tmsh_compare(cmd: str, first: Device, second: Device) -> str:
    """Get unified diff from tmsh command executed on 2 devices."""
    if not cmd.startswith("tmsh "):
        raise InputError
    diff = unified_diff(
        *[
            device.ssh.run(cmd).stdout.splitlines(keepends=True)
            for device in (first, second)
        ]
    )
    return "".join(diff)


def compare_crontabs(first: Device, second: Device):
    """Get diff between cron job entries on both given devices."""
    return DeepDiff(get_crontabs(first), get_crontabs(second))
