import os
from copy import deepcopy

from journeys.config import Config
from journeys.modifier.conflict.as3ucs import As3ucs
from journeys.modifier.conflict.plugins.Pem import Pem
from journeys.modifier.dependency import DEFAULT_DEPENDENCIES
from journeys.modifier.dependency import DependencyMap
from journeys.utils.as3_ops import load_declaration
from journeys.utils.as3_ops import stringify_declaration

AS3_CONFIG_DIR = os.path.join(os.path.dirname(__file__), "configs")


def test_as3_pem():
    bigip_conf_path = os.path.join(AS3_CONFIG_DIR, "bigip-pem.conf")
    as3_source_path = os.path.join(AS3_CONFIG_DIR, "as3-pem.json")
    as3_pattern_path = os.path.join(AS3_CONFIG_DIR, "as3-pem-result.json")

    source_as3 = load_declaration(as3_source_path)
    pattern_as3 = load_declaration(as3_pattern_path)
    config = Config.from_conf(bigip_conf_path)
    mutable_config = deepcopy(config)
    mutable_as3 = deepcopy(source_as3)
    as3ucs = As3ucs(mutable_as3)
    irules = as3ucs.decode_as3_irules()

    pem_obj = Pem(
        config, DependencyMap(config, DEFAULT_DEPENDENCIES), source_as3, as3_source_path
    )
    pem_obj.adjust_objects(mutable_config, mutable_as3)

    as3ucs.encode_as3_irules(irules)

    assert stringify_declaration(pattern_as3) == stringify_declaration(mutable_as3)
