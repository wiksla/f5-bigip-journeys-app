from typing import Dict
from typing import List

from f5.bigip.tm.ltm.node import Node
from f5.bigip.tm.ltm.pool import Members
from f5.bigip.tm.ltm.pool import Pool

from journeys.utils.device import Device
from journeys.validators.helpers import convert_raw_to_dict


def get_ltm_vs_status(device: Device) -> dict:
    """Get status of LTM Virtual Server."""
    ret_dict = {}
    for vs in device.icontrol.mgmt.tm.ltm.virtuals.get_collection():
        stats = vs.stats.load().to_dict()
        ret_dict[vs.name] = {}
        for url in stats["entries"]:
            ret_dict[vs.name]["status.availabilityState"] = stats["entries"][url][
                "nestedStats"
            ]["entries"]["status.availabilityState"]
            ret_dict[vs.name]["status.enabledState"] = stats["entries"][url][
                "nestedStats"
            ]["entries"]["status.enabledState"]
            ret_dict[vs.name]["status.statusReason"] = stats["entries"][url][
                "nestedStats"
            ]["entries"]["status.statusReason"]

    return ret_dict


def get_nodes_collection(device) -> List[Node]:
    """Get f5-sdk Collection obj of ltm nodes."""
    return device.icontrol.mgmt.tm.ltm.nodes.get_collection()


def get_ltm_nodes(device: Device) -> List[Dict]:
    """Get [{all iControl node items}] with all nodes."""
    collection = get_nodes_collection(device)
    return [convert_raw_to_dict(item.raw) for item in collection]


def get_ltm_nodes_state(device: Device) -> Dict:
    """Get  {node name: node state} for all nodes."""
    collection = get_nodes_collection(device)
    return {item.name: item.state for item in collection}


def get_pools_collection(device: Device) -> List[Pool]:
    """Get f5-sdk Collection obj of ltm Pool."""
    return device.icontrol.mgmt.tm.ltm.pools.get_collection()


def _get_ltm_pools(device: Device) -> List[Dict]:
    collection = get_pools_collection(device)
    return [convert_raw_to_dict(item.raw) for item in collection]


def get_pool_members_collection(pool: Pool) -> List[Members]:
    """Get f5-sdk Collection obj of ltm Members."""
    return pool.members_s.get_collection()


def get_ltm_pool_members_state(pool: Pool) -> Dict:
    """Get {member name: member state} for all pool members."""
    collection = get_pool_members_collection(pool)
    return {item.name: item.state for item in collection}


def get_ltm_pools_state(device: Device) -> Dict:
    """Get statuses of LTM pools and their members."""
    pools = get_pools_collection(device)
    return {pool.name: get_ltm_pool_members_state(pool) for pool in pools}
