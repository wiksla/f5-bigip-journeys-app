from .configs import build_config
from .configs import parse_config


def test_build_nested_and_multiple_args():
    payload = build_config(config_json_file="basic/single_obj_single_flag.json")
    assert payload == parse_config("basic/single_obj_single_flag.conf")
