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
    delete_file(device=device, remote=remote_mprov_cfg_location)
    return mprov_check_result


def create_mprov_cfg_locally(config_path: str):
    ucs_reader = UcsReader(extracted_ucs_dir=os.path.join(config_path))
    local_mprov_cfg_path = "/tmp/mprov.cfg"

    build_mprov_cfg(
        mprov_path=local_mprov_cfg_path,
        platform=ucs_reader.get_platform(),
        provisioned_modules=ucs_reader.get_provisioned_modules(),
        extramb=ucs_reader.get_config().bigdb.get(
            section="Provision.extraMB", option="value"
        ),
    )

    return local_mprov_cfg_path


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
