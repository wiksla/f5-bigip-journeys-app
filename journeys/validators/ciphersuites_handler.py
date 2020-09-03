from typing import Dict
from typing import List
from typing import Tuple

from journeys.utils.device import Device


def _get_raw_suites(device: Device) -> str:
    """Get unified diff from tmsh command executed on 2 devices."""
    cmd = "tmm --clientciphers 'DEFAULT'"
    return device.ssh.run(cmd).stdout


def _parse_header(line: str) -> Tuple[str]:
    return tuple(line.split())


def _remove_row_numbering(line: str) -> str:
    return line.lstrip().lstrip("0123456789:")


def _parse_suite_row(line: str) -> Tuple[str]:
    row = _remove_row_numbering(line)
    return tuple(row.split())


def get_ciphersuites(device: Device) -> List[Dict]:
    """Retrieve availavble ciphersuites from 'DEFAULT' profile."""
    ciphersuites = _get_raw_suites(device).splitlines(keepends=True)
    header_keys = _parse_header(ciphersuites[0])
    ciphersuites = ciphersuites[1:]
    return [
        {key: value for key, value in zip(header_keys, _parse_suite_row(suite))}
        for suite in ciphersuites
    ]


def get_ciphersuites_from_devices(first: Device, second: Device) -> List:
    """Return modules footprint for both devices."""
    return [get_ciphersuites(device) for device in (first, second)]
