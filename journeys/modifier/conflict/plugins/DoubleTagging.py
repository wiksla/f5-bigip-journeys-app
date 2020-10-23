from typing import Dict

from journeys.config import Config
from journeys.modifier.conflict.plugins.Plugin import TYPE_NOT_SUPPORTED
from journeys.modifier.conflict.plugins.Plugin import Plugin
from journeys.modifier.conflict.plugins.Plugin import find_objects_with_field_name
from journeys.modifier.dependency import DependencyMap


class DoubleTagging(Plugin):
    ID: str = "DoubleTagging"
    MSG_TYPE: str = TYPE_NOT_SUPPORTED
    MSG_INFO: str = "customer tag"

    def __init__(
        self,
        config: Config,
        dependency_map: DependencyMap,
        as3_declaration: Dict,
        as3_file_name: str,
    ):
        super().__init__(
            config,
            dependency_map,
            find_objects_with_field_name(
                config=config, type_matcher=("net", "vlan"), field_name="customer-tag"
            ),
            as3_declaration=as3_declaration,
            as3_file_name=as3_file_name,
        )

    def delete_objects(self, mutable_config: Config, mutable_as3_declaration: Dict):
        for obj_id in self.objects:
            obj = mutable_config.fields.get(obj_id)
            for int_field in obj.fields:
                if int_field.key == "customer-tag":
                    int_field.delete()
