import json
import logging
import os
from collections import OrderedDict
from json import JSONDecodeError
from pathlib import Path
from time import gmtime
from time import strftime
from typing import Dict

import click

from journeys.errors import JourneysError
from journeys.utils.device import Device
from journeys.validators.comparers import compare_db
from journeys.validators.comparers import compare_memory_footprint
from journeys.validators.comparers import tmsh_compare
from journeys.validators.core_watcher import list_cores
from journeys.validators.deployment import get_mcp_status
from journeys.validators.deployment import get_tmm_global_status
from journeys.validators.deployment import wait_for_prompt_state
from journeys.validators.ltm_checks import get_ltm_vs_status
from journeys.workdir import WORKDIR

PASSED = "PASSED"
FAILED = "FAILED"
USER_EVALUATION = "FOR_USER_EVALUATION"


log = logging.getLogger(__name__)


def cli_mcp_status_check(destination: Device, output, **kwargs) -> Dict:
    mcp_status = get_mcp_status(bigip=destination)
    click.echo(f"MCPD status:\n{json.dumps(mcp_status, indent=4)}", file=output)
    if (
        not mcp_status["last-load"] == "full-config-load-succeed"
        and mcp_status["phase"] == "running"
    ):
        click.echo("MCP down", file=output)
        return {"result": FAILED, "value": mcp_status}

    return {"result": PASSED, "value": mcp_status}


def cli_tmm_status_check(destination: Device, output, **kwargs) -> Dict:
    tmm_status = get_tmm_global_status(bigip=destination)
    click.echo(f"TMM status:\n{json.dumps(tmm_status, indent=4)}", file=output)
    return {"result": USER_EVALUATION, "value": tmm_status}


def cli_prompt_state_check(destination: Device, output, **kwargs) -> Dict:
    if not wait_for_prompt_state(device=destination):
        click.echo("Prompt is not active/standby", file=output)
        return {"result": FAILED, "value": False}
    return {"result": PASSED, "value": True}


def cli_core_dumps_check(destination: Device, output, **kwargs) -> Dict:
    try:
        list_cores(destination, raise_exception=True)
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


def cli_compare_db_check(source: Device, destination: Device, output) -> Dict:
    db_diff = compare_db(first=source, second=destination)
    click.echo(f"Sys DB diff:\n{db_diff.pretty()}", file=output)
    return {"result": USER_EVALUATION}


def cli_memory_footprint_check(source: Device, destination: Device, output) -> Dict:
    module_diff = compare_memory_footprint(first=source, second=destination)
    click.echo(f"Memory footprint diff:\n{module_diff.pretty()}", file=output)
    return {"result": USER_EVALUATION, "value": module_diff.to_json()}


def cli_ltm_vs_check(destination: Device, output, **kwargs) -> Dict:
    vs_status = get_ltm_vs_status(device=destination)
    click.echo(f"VS status:\n{json.dumps(vs_status, indent=4)}", file=output)
    return {"result": USER_EVALUATION, "value": vs_status}


def cli_version_diff_check(source: Device, destination: Device, output) -> Dict:
    version_diff = tmsh_compare(
        cmd="tmsh show sys version", first=source, second=destination
    )
    click.echo(f"tmsh show sys version diff:\n{version_diff}", file=output)
    return {"result": USER_EVALUATION, "value": version_diff}


def run_diagnose(checks: OrderedDict, kwargs: Dict, output_json: str) -> dict:
    results = {}
    for check_name, check_method in checks.items():
        click.echo(f"Running check: {check_name}")
        results[check_name] = check_method(**kwargs)

    if results:
        Path(output_json).write_text(json.dumps(results))

    return results


def exclude_checks(checks: Dict, excluded_checks: str):
    checks = OrderedDict(checks)
    try:
        exclude = json.loads(excluded_checks)
        for item in exclude:
            try:
                checks.pop(item)
            except KeyError:
                click.echo(
                    f"Validation method to exclude not found: {item}\n"
                    f"Check Documentation for allowed names."
                )
        return checks
    except JSONDecodeError as js_err:
        click.echo(
            f"Given option is not a valid JSON: {js_err}"
            "If you want to exclude single check, place it within list brackets"
            ",\neg. '[\"TMM status\"]'"
        )
        raise JourneysError(js_err)
    except TypeError as t_err:
        click.echo(
            "Given checks' names to exclude are not iterable.\n"
            "If you want to exclude single check, place it within list brackets"
            ",\neg. '[\"TMM status\"]'"
        )
        raise JourneysError(t_err)


def run_auto_checks(destination: Device, checks: OrderedDict):
    prefix = "autocheck_diagnose_output"
    timestamp = strftime("%Y%m%d%H%M%S", gmtime())
    output_log = os.path.join(WORKDIR, f"{prefix}_{timestamp}.log")
    output_json = os.path.join(WORKDIR, f"{prefix}_{timestamp}.json")
    check_success = True
    with open(output_log, "w") as logfile:
        kwargs = {"destination": destination, "output": logfile}
        diagnose_result = run_diagnose(
            checks=checks, kwargs=kwargs, output_json=output_json,
        )
        try:
            click.echo(
                f"Log watcher output:\n"
                f"{json.dumps(diagnose_result['Log watcher']['value'], indent=4)}",
                file=logfile,
            )
        except KeyError:
            log.error("No results from Log Watcher.")
    fails = []
    for check, result in diagnose_result.items():
        if result["result"] == FAILED:
            check_success = False
            fails.append(check)
    click.echo("Diagnostics finished.")
    if check_success:
        click.echo("No known issues have been found.")
        click.echo("Please check output logs to do more detailed results evaluation.")
    else:
        click.echo(
            f"Diagnostics failures found in {', '.join(fails)}. Please check output "
            f"logs for details."
        )
    return check_success


default_checks = OrderedDict()
default_checks["MCP status"] = cli_mcp_status_check
default_checks["TMM status"] = cli_tmm_status_check
default_checks["Prompt state"] = cli_prompt_state_check
default_checks["Core dumps"] = cli_core_dumps_check
default_checks["DB compare"] = cli_compare_db_check
default_checks["Memory footprint"] = cli_memory_footprint_check
default_checks["Version check"] = cli_version_diff_check
default_checks["LTM VS check"] = cli_ltm_vs_check

auto_checks = OrderedDict()
auto_checks["MCP status"] = cli_mcp_status_check
auto_checks["TMM status"] = cli_tmm_status_check
auto_checks["Prompt state"] = cli_prompt_state_check
auto_checks["Core dumps"] = cli_core_dumps_check
