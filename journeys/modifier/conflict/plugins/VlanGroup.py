from journeys.config import Config
from journeys.modifier.conflict.plugins.Plugin import TYPE_NOT_SUPPORTED
from journeys.modifier.conflict.plugins.Plugin import Plugin
from journeys.modifier.conflict.plugins.Plugin import find_object_with_type_match
from journeys.modifier.dependency import DependencyMap


class VlanGroup(Plugin):
    ID: str = "VlanGroup"
    MSG_TYPE: str = TYPE_NOT_SUPPORTED
    MSG_INFO: str = "vlan-group"

    def __init__(self, config: Config, dependency_map: DependencyMap):
        super().__init__(
            config,
            dependency_map,
            find_object_with_type_match(
                config=config, type_matcher=("net", "vlan-group")
            ),
        )
