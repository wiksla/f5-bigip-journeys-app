import deepdiff

from journeys.utils.device import Device
from journeys.validators.helpers import convert_raw_to_dict


def compare_db(first: Device, second: Device):
    """Run DeepDiff against devices' DBs."""
    return deepdiff.DeepDiff(*get_dbs_from_devices(first, second))


def get_all_dbs_raw(device: Device) -> dict:
    """Return dict of modified Db objects."""
    collection = device.icontrol.mgmt.tm.sys.dbs.get_collection()
    raw_dbs = {item.name: convert_raw_to_dict(item.raw) for item in collection}
    return raw_dbs


def get_dbs_from_devices(first: Device, second: Device) -> list:
    """Get list of DBs from both devices."""
    return [get_all_dbs_raw(device) for device in (first, second)]
