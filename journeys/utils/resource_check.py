import os
import tempfile

from fabric import Result

from journeys.utils.device import Device
from journeys.utils.device import delete_file
from journeys.utils.device import put_file
from journeys.utils.ucs_reader import UcsReader

MPROV_FN = "mprov.cfg"


def ensure_if_minimum_resources_are_met_on_destination(
    config_path: str, device: Device
) -> str:
    ucs_reader = UcsReader(extracted_ucs_dir=os.path.join(config_path))
    with tempfile.NamedTemporaryFile() as tmp_file:
        build_mprov_cfg(
            mprov_path=tmp_file.name,
            platform=ucs_reader.get_platform(),
            provisioned_modules=ucs_reader.get_provisioned_modules(),
            extramb=ucs_reader.get_config().bigdb.get(
                section="Provision.extraMB", option="value"
            ),
        )
        remote_mprov_cfg_location = f"/root/{MPROV_FN}"
        put_file(device=device, local=tmp_file.name, remote=remote_mprov_cfg_location)
    mprov_check_result = check_mprov_cfg(
        device=device, mprov_cfg_location=remote_mprov_cfg_location
    )
    delete_file(device=device, location=remote_mprov_cfg_location)
    return mprov_check_result


def build_mprov_cfg(mprov_path: str, platform: str, provisioned_modules: dict, extramb):
    with open(mprov_path, "w+") as cnf:
        cnf.write(f"provision.platform={platform}\n")
        for module, level in provisioned_modules.items():
            cnf.write(f"provision.level.{module}={level}\n")
        cnf.write(f"provision.extramb={extramb}")


def check_mprov_cfg(device: Device, mprov_cfg_location: str) -> str:
    result = device.ssh.run(
        cmd=f"mprov.pl --list --file={mprov_cfg_location}", raise_error=False
    )
    if result.stderr:
        error_msg = _parse_stderr(result)
        if error_msg:
            return error_msg
    return "Minimum recommended requirements for resources are met."


def _parse_stderr(result: Result) -> str:
    message = ""
    for line in result.stderr.splitlines():
        if "limit exceeded" in line:
            message += line.replace("'", "") + "\n"
    if message:
        message = (
            "Minimum recommended requirements for resources are not met.\n" + message
        )
    return message[:-1]


# TODO: below may be obsolete (need verification)
def obtain_source_resources(device: Device) -> dict:
    return device.ssh.run_transaction(
        cmds=[
            ("disk", "tmsh show /sys hardware field-fmt", _obtain_disk_size),
            ("ram", "tmsh show /sys memory field-fmt", _obtain_memory),
            ("cores", "tmsh show /sys hardware field-fmt", _obtain_cpu_cores_no),
        ],
    )


def _obtain_disk_size(result):
    result = result.stdout.splitlines()
    for idx, line in enumerate(result):
        if "versions.2.name Size" == line.lstrip():
            return result[idx + 1].lstrip().split()[-1]


def _obtain_cpu_cores_no(result):
    result = result.stdout.splitlines()
    for idx, line in enumerate(result):
        if "versions.1.name cores" == line.lstrip():
            return result[idx + 1].lstrip().split()[1]


def _obtain_memory(result):
    for line in result.stdout.splitlines():
        line = line.lstrip()
        if line.startswith("memory-total"):
            return line.split()[-1]