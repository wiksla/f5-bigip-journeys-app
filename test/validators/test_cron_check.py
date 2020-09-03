from journeys.validators.cron_check import get_all_periodic_jobs
from journeys.validators.cron_check import get_anacron_jobs
from journeys.validators.cron_check import get_crontabs
from journeys.validators.cron_check import get_etc_crontab_entries
from journeys.validators.cron_check import get_sys_users


def test_get_all_sys_users(bigip_mock):
    """Check fetching all sys users"""
    users = get_sys_users(bigip_mock)
    assert type(users) == list
    assert "admin" in users


def test_get_crontabs_for_users(bigip_mock):
    """Check fetching jobs for all users"""
    cron_dict = get_crontabs(bigip_mock)
    assert type(cron_dict) == dict
    assert "admin" in cron_dict
    assert cron_dict["admin"][0].startswith("51")


def test_get_anacron_jobs(bigip_mock):
    """Get cron jobs from cron.* directories that are executed with anacron."""
    anacron_jobs = get_anacron_jobs(bigip_mock)
    assert type(anacron_jobs) == dict
    assert len(anacron_jobs) == 4
    assert "integritycheck" in anacron_jobs["cron.daily"]
    assert "5checkcert" in anacron_jobs["cron.weekly"]
    assert not anacron_jobs["cron.monthly"]


def test_get_etc_crontab_entries(bigip_mock):
    """Check fetching entries from /etc/crontab."""
    crontab = get_etc_crontab_entries(bigip_mock)
    assert crontab["/etc/crontab"] == []


def test_get_all_cron_jobs(bigip_mock):
    """Check fetching all cron jobs."""
    jobs = get_all_periodic_jobs(bigip_mock)
    assert "admin" in jobs
    assert "cron.daily" in jobs
    assert "/etc/crontab" in jobs
