from typing import Dict

from journeys.config import Config
from journeys.modifier.conflict.plugins.Plugin import FIELD_NOT_SUPPORTED
from journeys.modifier.conflict.plugins.Plugin import Plugin
from journeys.modifier.conflict.plugins.Plugin import find_objects_with_field_name
from journeys.modifier.dependency import DependencyMap


class WildcardWhitelist(Plugin):
    ID: str = "WildcardWhitelist"
    MSG_TYPE: str = FIELD_NOT_SUPPORTED

    def __init__(
        self,
        config: Config,
        dependency_map: DependencyMap,
        as3_declaration: Dict,
        as3_file_name: str,
    ):
        super().__init__(
            config=config,
            dependency_map=dependency_map,
            objects=find_objects_with_field_name(
                config=config,
                type_matcher=("security", "dos", "network-whitelist"),
                field_name="extended-entries",
            ),
            as3_declaration=as3_declaration,
            as3_file_name=as3_file_name,
        )
