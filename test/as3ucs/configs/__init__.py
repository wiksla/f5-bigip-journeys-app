import os

from journeys.as3ucs.as3ucs import As3ucs
from journeys.config import Config

AS3_CONFIG_DIR = os.path.dirname(__file__)


def process_as3_test_helper(source_conf, source_as3, pattern_as3):
    source_conf_path = os.path.join(AS3_CONFIG_DIR, source_conf)
    source_as3_path = os.path.join(AS3_CONFIG_DIR, source_as3)
    pattern_as3_path = os.path.join(AS3_CONFIG_DIR, pattern_as3)

    as3_source = As3ucs(source_as3_path)
    as3_pattern = As3ucs(pattern_as3_path)
    config = Config.from_conf(source_conf_path)
    pattern_str = as3_pattern.get_declaration_string()
    as3_source.process_ucs_changes(config)
    result_str = as3_source.get_declaration_string()

    assert pattern_str == result_str
