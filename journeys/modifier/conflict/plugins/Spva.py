from journeys.config import Config
from journeys.modifier.conflict.plugins.Plugin import TYPE_NOT_SUPPORTED
from journeys.modifier.conflict.plugins.Plugin import Plugin
from journeys.modifier.conflict.plugins.Plugin import find_object_with_type_match
from journeys.modifier.dependency import DependencyMap


class SPVA(Plugin):
    ID: str = "SPVA"
    MSG_TYPE: str = TYPE_NOT_SUPPORTED
    MSG_INFO: str = "SPVA"

    def __init__(self, config: Config, dependency_map: DependencyMap):
        objects = (
            find_object_with_type_match(
                config=config, type_matcher=("net", "address-list")
            )
            | find_object_with_type_match(
                config=config, type_matcher=("security", "firewall", "address-list")
            )
            | find_object_with_type_match(
                config=config,
                type_matcher=("security", "shared-objects", "address-list"),
            )
        )

        super().__init__(config, dependency_map, objects)

        print(self.dependencies)
