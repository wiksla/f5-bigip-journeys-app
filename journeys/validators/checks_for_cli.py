import json
from collections import OrderedDict
from pathlib import Path
from typing import Dict

import click

from journeys.utils.device import Device
from journeys.validators.comparers import compare_db
from journeys.validators.comparers import compare_memory_footprint
from journeys.validators.comparers import tmsh_compare
from journeys.validators.core_watcher import list_cores
from journeys.validators.deployment import get_mcp_status
from journeys.validators.deployment import get_tmm_global_status
from journeys.validators.deployment import wait_for_prompt_state
from journeys.validators.exceptions import JourneysError
from journeys.validators.ltm_checks import get_ltm_vs_status

PASSED = "PASSED"
FAILED = "FAILED"
USER_EVALUATION = "FOR_USER_EVALUATION"


def cli_mcp_status_check(destination: Device, output: str, **kwargs) -> Dict:
    mcp_status = get_mcp_status(bigip=destination)
    click.echo(f"MCPD status:\n{json.dumps(mcp_status, indent=4)}", file=output)
    if (
        not mcp_status["last-load"] == "full-config-load-succeed"
        and mcp_status["phase"] == "running"
    ):
        click.echo("MCP down", file=output)
        return {"result": FAILED, "value": mcp_status}

    return {"result": PASSED, "value": mcp_status}


def cli_tmm_status_check(destination: Device, output: str, **kwargs) -> Dict:
    tmm_status = get_tmm_global_status(bigip=destination)
    click.echo(f"TMM status:\n{json.dumps(tmm_status, indent=4)}", file=output)
    return {"result": USER_EVALUATION, "value": tmm_status}


def cli_prompt_state_check(destination: Device, output: str, **kwargs) -> Dict:
    if not wait_for_prompt_state(device=destination):
        click.echo("Prompt is not active/standby", file=output)
        return {"result": FAILED, "value": False}
    return {"result": PASSED, "value": True}


def cli_core_dumps_check(destination: Device, output: str, **kwargs) -> Dict:
    try:
        click.echo(list_cores(destination, raise_exception=True))
        click.echo(
            "No core dumps found in /var/core\n" "Core dumps check PASSED.\n",
            file=output,
        )
        return {"result": PASSED}
    except JourneysError as err:
        click.echo(
            f"{err}\n"
            f"Diagnostic core dumps found. You can check why it happened\n"
            "and read more bout it at:\n"
            "https://support.f5.com/csp/article/K10062\n\n"
            "Core dupms check FAILED.\n"
        )
        return {"result": FAILED}


def cli_compare_db_check(source: Device, destination: Device, output: str) -> Dict:
    db_diff = compare_db(first=source, second=destination)
    click.echo(f"Sys DB diff:\n{db_diff.pretty()}", file=output)
    return {"result": USER_EVALUATION}


def cli_memory_footprint_check(
    source: Device, destination: Device, output: str
) -> Dict:
    module_diff = compare_memory_footprint(first=source, second=destination)
    click.echo(f"Memory footprint diff:\n{module_diff.pretty()}", file=output)
    return {"result": USER_EVALUATION, "value": module_diff}


def cli_ltm_vs_check(destination: Device, output: str, **kwargs) -> Dict:
    vs_status = get_ltm_vs_status(device=destination)
    click.echo(vs_status, file=output)
    return {"result": USER_EVALUATION, "value": vs_status}


def cli_version_diff_check(source: Device, destination: Device, output: str) -> Dict:
    version_diff = tmsh_compare(
        cmd="tmsh show sys version", first=source, second=destination
    )
    click.echo(f"tmsh show sys version diff:\n{version_diff}", file=output)
    return {"result": USER_EVALUATION, "value": version_diff}


def run_diagnose(checks: OrderedDict, kwargs: Dict, output_json: str) -> None:
    results = {}
    for check_name, check_method in checks.items():
        click.echo(f"Running check: {check_name}")
        results[check_name] = check_method(**kwargs)

    if results:
        (Path("/migrate") / output_json).write_text(json.dumps(results))


default_checks = OrderedDict()
default_checks["MCP status"] = cli_mcp_status_check
default_checks["TMM status"] = cli_tmm_status_check
default_checks["Prompt state"] = cli_prompt_state_check
default_checks["Core dumps"] = cli_core_dumps_check
default_checks["DB compare"] = cli_compare_db_check
default_checks["Memory footprint"] = cli_memory_footprint_check
default_checks["Version check"] = cli_version_diff_check
default_checks["cli_ltm_vs_check"] = cli_ltm_vs_check

auto_checks = OrderedDict()
auto_checks["MCP status"] = cli_mcp_status_check
auto_checks["TMM status"] = cli_tmm_status_check
auto_checks["Prompt state"] = cli_prompt_state_check
auto_checks["Core dumps"] = cli_core_dumps_check