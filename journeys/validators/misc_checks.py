import logging

from journeys.utils.device import Device

log = logging.getLogger(__name__)


def run_sys_eicheck(device: Device) -> int:
    """Get result of /usr/libexec/sys-eicheck.py execution."""
    cmd = "python /usr/libexec/sys-eicheck.py"
    result = device.ssh.run(cmd)
    if result.stderr:
        log.error(result.stderr)
    if result.exited:
        log.error(result.stdout)
    else:
        log.debug(result.stdout)
    return result.exited
