from typing import Dict
from typing import List

import deepdiff
from pyparsing import Word
from pyparsing import alphas
from pyparsing import nums

from journeys.utils.device import Device


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
    return deepdiff.DeepDiff(*get_modules_footprint_from_devices(first, second))
