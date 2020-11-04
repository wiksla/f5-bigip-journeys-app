from typing import Dict
from typing import List

from deepdiff import DeepDiff

from journeys.utils.device import Device


def get_sys_users(device: Device) -> List[str]:
    """Get system users."""
    users_output = device.ssh.run("cut -d: -f1 /etc/passwd")
    return [user for user in users_output.stdout.splitlines()]


def compare_crontabs(first: Device, second: Device):
    """Get diff between cron job entries on both given devices."""
    return DeepDiff(get_crontabs(first), get_crontabs(second))


def _get_crontabs_for_users(device: Device, users: List[str]) -> Dict:
    """Get content of 'crontab -l -u' for given users."""
    users_jobs = {}
    for user in users:
        crontab_resp = device.ssh.run(f"crontab -l -u {user}", raise_error=False)
        if not crontab_resp.exited:
            crontab = crontab_resp.stdout.splitlines(keepends=False)
            users_jobs[user] = []
            for line in crontab:
                if _has_non_cron_entry(line):
                    continue
                if line:
                    users_jobs[user].append(line)
    return users_jobs


def get_crontabs(device: Device) -> Dict:
    """Return dict with system users as keys and lists of cron jobs as values."""
    return _get_crontabs_for_users(device, get_sys_users(device))


def get_etc_crontab_entries(device: Device) -> Dict:
    """Return contents of /etc/crontab assigned to such key."""
    crontab = device.ssh.run("cat /etc/crontab").stdout.splitlines(keepends=False)
    ret = []
    for line in crontab:
        if _has_non_cron_entry(line):
            continue
        if line:
            ret.append(line)
    return {"/etc/crontab": ret}


def get_anacron_jobs(device: Device) -> Dict:
    """List scripts executed by anacron from cron.* directories."""
    periods = ["hourly", "daily", "weekly", "monthly"]
    return {
        f"cron.{period}": device.ssh.run(f"ls -1 /etc/cron.{period}").stdout.splitlines(
            keepends=False
        )
        for period in periods
    }


def get_all_periodic_jobs(device: Device) -> Dict:
    """Get all jobs from crontabs, anacron and /etc/crontab merged into one dict."""
    jobs = {}
    jobs.update(get_crontabs(device))
    jobs.update(get_anacron_jobs(device))
    jobs.update(get_etc_crontab_entries(device))
    return jobs


def _has_non_cron_entry(line: str) -> bool:
    excluded_phrases = ("#", "PATH", "SHELL", "MAILTO")
    return list(filter(line.startswith, excluded_phrases)) != []
