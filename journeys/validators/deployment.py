import logging
import re
import time

import click

from journeys.errors import JourneysError
from journeys.errors import UcsActionError
from journeys.utils.device import Device
from journeys.utils.device import save_ucs

log = logging.getLogger(__name__)


def run_backup(bigip: Device, ucs_passphrase: str, is_user_triggered=False) -> str:
    prefix = "user" if is_user_triggered else "auto"
    timestamp = time.strftime("%Y%m%d%H%M%S", time.gmtime())
    ucs_name = f"{prefix}_backup_from_{timestamp}.ucs"
    try:
        save_ucs(bigip, ucs_name, ucs_passphrase)
    except UcsActionError:
        raise UcsActionError(action_name="Saving backup Ucs")

    return ucs_name


def backup_over_cli(destination: Device, ucs_passphrase=""):
    click.echo("Creating auto backup.")
    backed_up = run_backup(destination, ucs_passphrase, is_user_triggered=True)
    restore_command = format_restore_backup_command(
        ucs=backed_up, ucs_passphrase=ucs_passphrase
    )
    click.echo(
        "Backup created.\n In case of emergency you can restore it on the "
        f"Destination System platform by running: \n {restore_command}'"
    )


def format_restore_backup_command(ucs: str, ucs_passphrase: str):
    cmd = f"tmsh load sys ucs {ucs}"
    if ucs_passphrase:
        cmd += f" passphrase {ucs_passphrase}"

    return cmd


def get_mcp_status(bigip: Device) -> dict:
    """Get status of MCP."""
    cmd = "tmsh show sys mcp-state field-fmt"
    properties = {"last-load", "phase", "end-platform-id-received"}
    return _get_field_formatted_property(bigip, cmd, properties)


def get_tmm_global_status(bigip: Device) -> dict:
    """Get status of TMM."""
    cmd = "tmsh show sys tmm-info field-fmt global"
    properties = {
        "five-min-avg-usage-ratio",
        "five-sec-avg-usage-ratio",
        "memory-total",
        "memory-used",
        "npus",
        "one-min-avg-usage-ratio",
    }
    return _get_field_formatted_property(bigip, cmd, properties)


def wait_for_prompt_state(
    device: Device, states=None, timeout=480, valid_states_required=5, interval=4
) -> bool:
    """Wait for desired /var/prompt/ps1 state.
    valid_state_count was introduced to ensure that desired state is stable.
    :param device:
    :param states: list of desired ps1 states.
    :param timeout:
    :param valid_states_required:
    :param interval
    :return: True for success or False otherwise.
    """
    states = states or [
        "Active",
        "ForcedOffline",
        "Standby",
        "Peer Time Out of Sync",
        "TimeLimitedModulesActive",
    ]
    end_time = time.time() + timeout
    valid_state_count = 0
    while time.time() < end_time:
        prompt_state = _get_prompt_status(device)
        log.debug("Prompt State: {}".format(prompt_state))
        if prompt_state in states:
            valid_state_count += 1
            log.debug("wait_for_prompt_state.valid_state_count: %d", valid_state_count)
            if valid_state_count == valid_states_required:
                log.info(f"Prompt state: {prompt_state}")
                return True
            time.sleep(interval)
        elif prompt_state == "REBOOT REQUIRED":
            log.info(f"Reboot required for device: {device.host}")
            return True
        else:
            valid_state_count = 0
            log.debug("wait_for_prompt_state.valid_state_count: %d", valid_state_count)
            time.sleep(interval * 2)
    return False


def _get_prompt_status(device: Device):
    result = device.ssh.run("cat /var/prompt/ps1")
    if result.exited == 0:
        prompt_state = result.stdout.strip()
        prompt_state = prompt_state.replace("Eval", "")
        if prompt_state.startswith("/S") or ":" in prompt_state:
            return "".join(prompt_state.split(":")[1:])
        else:
            return prompt_state
    return None


def _get_field_formatted_property(bigip: Device, cmd: str, properties: set) -> dict:
    if "field-fmt" not in cmd:
        raise JourneysError()
    result = bigip.ssh.run(cmd)
    if not result.exited:
        ret_dict = {}
        stdout_split = result.stdout.split()
        for key in properties:
            key_index = stdout_split.index(key)
            ret_dict[key] = stdout_split[key_index + 1]
        return ret_dict
    raise JourneysError(
        f"Can't get {cmd} - returned: {result.stdout}, "
        f"err: {result.stderr}, exit_code: {result.exited}"
    )


def _get_db_raw(bigip: Device) -> str:
    """Return stdout from 'tmsh list sys db all-properties one-line'."""
    cmd = "tmsh list sys db all-properties one-line"
    return bigip.ssh.run(cmd=cmd).stdout


def _obtain_entry_key(line: str) -> str:
    """Obtain db variable name from db entry in one-line format."""
    return line.split()[2]


def _obtain_entry_properties(line: str) -> list:
    """Acquire all properties from db entry in one-line format."""
    return re.findall(r"(\S*?) \"(.*?)\"", line)


def _create_dictionary_from_entry_properties(line: str) -> dict:
    """Parse one db entry in one-line format to dict."""
    properties_dictionary = {}
    for key, value in _obtain_entry_properties(line):
        properties_dictionary[key] = value
    return properties_dictionary
