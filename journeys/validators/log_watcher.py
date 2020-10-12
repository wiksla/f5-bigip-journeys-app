import logging
import re
import tempfile
from pathlib import Path
from re import Pattern
from typing import Dict
from typing import List

from journeys.utils.device import Device
from journeys.utils.device import get_file
from journeys.utils.device import stat_file
from journeys.validators.checks_for_cli import USER_EVALUATION
from journeys.validators.exceptions import JourneysError
from journeys.workdir import WORKDIR

log = logging.getLogger(__name__)


default_watchers = {
    "/var/log/ltm": "([eE][rR][rR])|([cC][rR][iI][tT])",
    "/var/log/apm": "([eE][rR][rR])|([cC][rR][iI][tT])",
    "/var/log/gtm": "([eE][rR][rR])|([cC][rR][iI][tT])",
    "/var/log/tmm": "([eE][rR][rR])|([cC][rR][iI][tT])",
    "/var/log/liveinstall.log": "([eE][rR][rR])|([cC][rR][iI][tT])",
    "/var/log/asm": "([eE][rR][rR])|([cC][rR][iI][tT])",
    "/var/log/ts/bd.log": "([eE][rR][rR])|([cC][rR][iI][tT])",
    "/var/log/ts/asm_config_server.log": "([eE][rR][rR])|([cC][rR][iI][tT])",
    "/var/log/ts/pabnagd.log": "([eE][rR][rR])|([cC][rR][iI][tT])",
    "/var/log/ts/db_upgrade.log": "([eE][rR][rR])|([cC][rR][iI][tT])",
    "/var/log/daemon.log": "([eE][rR][rR])|([cC][rR][iI][tT])",
    "/var/log/kern.log": "([eE][rR][rR])|([cC][rR][iI][tT])",
    "/var/log/messages": "([eE][rR][rR])|([cC][rR][iI][tT])",
}


def _matches_pattern(line: str, regexes: List[Pattern]):
    for pattern in regexes:
        if pattern.search(line) is None:
            return False
    return True


class LogWatcher:
    """
    Class responsible for observing log changes. Can be used as context manager.
    If no logs are provided default watcher list is being used.
    """

    def __init__(self, device: Device, logs=None):
        if logs is None:
            logs = default_watchers
        self.__device = device
        self.__logs = {
            logfile: [re.compile(r) for r in regex]
            if isinstance(regex, list)
            else [re.compile(regex)]
            for (logfile, regex) in logs.items()
        }
        self.__tmpdir = tempfile.TemporaryDirectory(prefix="log_watcher_", dir=WORKDIR)
        self.__tmppath = Path(WORKDIR) / Path(self.__tmpdir.name)
        self.__stopped = False
        self._pointers = dict()
        self.__diff = dict()

    def __enter__(self):
        self.start()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.stop()

    def start(self):
        """Start logging."""
        for logfile, _ in self.__logs.items():
            try:
                log.debug(f"Checking size of file {logfile}")
                f = stat_file(self.__device, logfile)
                self._pointers[logfile] = f.st_size
            except FileNotFoundError:
                log.debug(f"{logfile} file does not exist. ")
            except PermissionError:
                log.debug(f"No required permission for file: {logfile}")
        log.info("Logging started")

    def stop(self):
        """Stop logging."""
        log.info("Stopping logging")
        for logfile, regexes in self.__logs.items():
            try:
                post_name = self.__tmppath / logfile.replace("/", "_")
                log.debug(f"Downloading file {logfile}")
                get_file(self.__device, logfile, str(post_name))

                with post_name.open() as f:
                    f.seek(self._pointers[logfile], 0)
                    self.__diff[logfile] = [
                        line
                        for line in f.readlines()
                        if _matches_pattern(line, regexes)
                    ]
            except FileNotFoundError:
                if logfile in self._pointers.keys():
                    log.error(f"{logfile} does not exist.")
                    self.__diff[logfile] = (
                        f"{logfile} does not exist on the Platform, "
                        f"but existed before deployment. "
                    )
            except PermissionError:
                log.debug(f"No required permission for file: {logfile}")

        self.__stopped = True
        self.__tmpdir.cleanup()
        log.info("Logging stopped")

    def get_diff(self) -> Dict[str, List[str]]:
        """Return diff of logs."""
        if not self.__stopped:
            raise JourneysError("LogWatcher not stopped")
        return self.__diff

    def get_log_watcher_result(self, output, **kwargs):
        diff = self.get_diff()
        result = USER_EVALUATION
        return {"result": result, "value": diff}
