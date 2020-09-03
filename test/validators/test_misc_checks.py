from journeys.validators.misc_checks import run_sys_eicheck


def test_get_eicheck(bigip_mock):
    assert run_sys_eicheck(bigip_mock) == 0
