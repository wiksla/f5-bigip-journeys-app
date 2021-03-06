import json
import logging
from collections import OrderedDict
from json import JSONDecodeError
from pathlib import Path
from typing import Dict

import click

from journeys.errors import CoreWatcherFailed
from journeys.errors import JourneysError
from journeys.errors import ValidationRuntimeError
from journeys.utils.device import Device
from journeys.validators.core_watcher import list_cores
from journeys.validators.db_comparer import compare_db
from journeys.validators.deployment import PROMPT_ERR_MSG
from journeys.validators.deployment import PROMPT_FEEDBACK
from journeys.validators.deployment import get_mcp_status
from journeys.validators.deployment import get_tmm_global_status
from journeys.validators.deployment import wait_for_prompt_state
from journeys.validators.helpers import pretty
from journeys.validators.helpers import tmsh_compare
from journeys.validators.log_watcher import LogWatcher
from journeys.validators.ltm_checks import get_ltm_vs_status
from journeys.validators.module_footprint_comparer import compare_memory_footprint

PASSED = "PASSED"
FAILED = "FAILED"
USER_EVALUATION = "FOR_USER_EVALUATION"


log = logging.getLogger(__name__)


def attributes(name: str, require_source: bool, require_root: bool):
    def wrapper(func):
        setattr(func, "name", name)
        setattr(func, "require_source", require_source)
        setattr(func, "require_root", require_root)
        if not func.__doc__:
            raise JourneysError("description missing")
        setattr(func, "description", func.__doc__)
        return func

    return wrapper


@attributes(
    name="MCP status", require_source=False, require_root=True,
)
def cli_mcp_status_check(destination: Device, output, **kwargs) -> Dict:
    """Checks if values of returned fields are correct. \
This method uses 'tmsh show sys mcp-state field-fmt' """
    try:
        mcp_status = get_mcp_status(bigip=destination)
    except ValidationRuntimeError as err:
        return {"result": FAILED, "info": "Failed to get mcp status", "debug": err}
    if (
        mcp_status["last-load"] == "full-config-load-succeed"
        and mcp_status["phase"] == "running"
    ):
        click.echo(
            f"MCPD status:\n{json.dumps(mcp_status, indent=4)}\n" f"result: {PASSED}",
            file=output,
        )
        return {"result": PASSED, "value": mcp_status}
    click.echo(
        f"MCPD down: \n{json.dumps(mcp_status, indent=4)}\n" f"result: {FAILED}",
        file=output,
    )
    return {"result": FAILED, "value": mcp_status}


@attributes(
    name="TMM status", require_source=False, require_root=True,
)
def cli_tmm_status_check(destination: Device, output, **kwargs) -> Dict:
    """Logs status of TMM. Requires manual evaluation."""
    try:
        tmm_status = get_tmm_global_status(bigip=destination)
    except ValidationRuntimeError as err:
        return {"result": FAILED, "info": "Failed to get tmm status", "debug": err}
    click.echo(f"TMM status:\n{json.dumps(tmm_status, indent=4)}", file=output)
    return {"result": USER_EVALUATION, "value": tmm_status}


@attributes(
    name="Prompt state", require_source=False, require_root=True,
)
def cli_prompt_state_check(destination: Device, output, **kwargs) -> Dict:
    """Checks if prompt state is in active mode."""
    PROMPT_RESULT_LOOKUP = {
        "Active": PASSED,
        "ForcedOffline": PASSED,
        "Standby": PASSED,
        "Peer Time Out of Sync": PASSED,
        "TimeLimitedModulesActive": PASSED,
        "REBOOT REQUIRED": USER_EVALUATION,
        "DOWN": FAILED,
    }
    prompt_state = wait_for_prompt_state(device=destination)
    info = PROMPT_FEEDBACK.get(prompt_state, PROMPT_ERR_MSG).format(
        state=prompt_state, host=destination.host
    )
    result = PROMPT_RESULT_LOOKUP.get(prompt_state, FAILED)
    click.echo(info, file=output)
    click.echo(f"Result: {result}", file=output)
    return {"result": result, "value": {"info": info, "state": prompt_state}}


@attributes(
    name="Core dumps", require_source=False, require_root=True,
)
def cli_core_dumps_check(destination: Device, output, **kwargs) -> Dict:
    """Checks if diagnostic core dumps were created."""
    try:
        list_cores(destination, raise_exception=True)
        click.echo("Core dumps check:", file=output)
        msg = "No core dumps found in /var/core\n" "Core dumps check PASSED."
        click.echo(msg, file=output)
        result = PASSED
    except CoreWatcherFailed as err:
        msg = f"{err}\n"
        "You can check why it happened\n"
        "and read more about it at:\n"
        "https://support.f5.com/csp/article/K10062"
        click.echo(msg, file=output)
        click.echo("Core dumps check FAILED.\n", file=output)
        result = FAILED
    finally:
        return {"result": result, "value": {"info": msg}}


@attributes(
    name="DB compare", require_source=True, require_root=False,
)
def cli_compare_db_check(source: Device, destination: Device, output) -> Dict:
    """Compares two system DBs getting them from iControl endpoint for sys db. \
Requires manual evaluation."""
    db_diff = compare_db(first=source, second=destination)
    root_name = "DB record "
    collection_name = "Sys DB"
    click.echo(
        f"Sys DB diff:\n{pretty(db_diff, root_name, collection_name)}", file=output
    )
    return {"result": USER_EVALUATION, "value": json.loads(db_diff.to_json())}


@attributes(
    name="Memory footprint", require_source=True, require_root=True,
)
def cli_memory_footprint_check(source: Device, destination: Device, output) -> Dict:
    """Compares information from 'tmsh show sys provision' for both systems. \
Requires manual evaluation. """
    root_name = "Module"
    collection_name = "provisioned modules"

    module_diff = compare_memory_footprint(first=source, second=destination)
    click.echo(
        f"Memory footprint diff:\n{pretty(module_diff, root_name, collection_name)}",
        file=output,
    )
    return {"result": USER_EVALUATION, "value": json.loads(module_diff.to_json())}


@attributes(
    name="LTM VS check", require_source=False, require_root=False,
)
def cli_ltm_vs_check(destination: Device, output, **kwargs) -> Dict:
    """Check lists of all defined LTM nodes and Virtual Servers configured in the new \
system."""
    vs_status = get_ltm_vs_status(device=destination)
    click.echo(f"VS status:\n{json.dumps(vs_status, indent=4)}", file=output)
    return {"result": USER_EVALUATION, "value": vs_status}


@attributes(
    name="Version check", require_source=True, require_root=True,
)
def cli_version_diff_check(source: Device, destination: Device, output) -> Dict:
    """Compares information from 'tmsh show sys version' for both systems. \
Requires manual evaluation."""
    version_diff = tmsh_compare(
        cmd="tmsh show sys version", first=source, second=destination
    )
    click.echo(f"tmsh show sys version diff:\n{version_diff}", file=output)
    return {"result": USER_EVALUATION, "value": {"unified_diff": version_diff}}


@attributes(
    name="Log watcher", require_source=False, require_root=True,
)
def cli_log_watcher_data_collector(destination: Device, output, **kwargs) -> dict:
    """Check looks for 'ERR' and 'CRIT' phrases (case insensitive) \
that appear in log during UCS deployment process."""
    try:
        lw = LogWatcher.init_from_saved_pointers(destination)
        lw.stop()
        diff = lw.get_diff()
        lw.cleanup()
        msg = (
            "Patterns representing potential errors found in logs. "
            f"Review them to find out details: \n{json.dumps(diff, indent=4)}"
            if any(diff.values())
            else "No 'ERR' and 'CRIT' phrases found in logs."
        )
        click.echo(f"Log Watcher check:\n{msg}", file=output)
        return {"result": USER_EVALUATION, "value": diff}
    except ValidationRuntimeError as err:
        click.echo(f"Failed to execute log watcher check: {err}\n")
        return {
            "result": FAILED,
            "value": {"info": str(err)},
        }


def run_diagnose(checks: OrderedDict, kwargs: Dict, output_json: str) -> dict:
    results = {}
    for check_name, check_method in checks.items():
        msg = f"Running check: {check_name}"
        click.echo(msg)
        log.debug(msg)
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


default_checks = OrderedDict()
default_checks["Prompt state"] = cli_prompt_state_check
default_checks["Log watcher"] = cli_log_watcher_data_collector
default_checks["MCP status"] = cli_mcp_status_check
default_checks["TMM status"] = cli_tmm_status_check
default_checks["Core dumps"] = cli_core_dumps_check
default_checks["DB compare"] = cli_compare_db_check
default_checks["Memory footprint"] = cli_memory_footprint_check
default_checks["Version check"] = cli_version_diff_check
default_checks["LTM VS check"] = cli_ltm_vs_check
