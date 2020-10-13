from pathlib import Path
from typing import List

from journeys.errors import JourneysError
from journeys.utils.device import Device
from journeys.utils.device import list_dir


def list_cores(device: Device, raise_exception=False) -> List[str]:
    """List cores found in /var/core directory on device."""
    files = list_dir(device=device, directory="/var/core/")
    cores = [Path(x).name for x in files if x.endswith("core.gz")]
    if cores and raise_exception:
        raise JourneysError(f"New cores found: {', '.join(cores)}")
    return cores
