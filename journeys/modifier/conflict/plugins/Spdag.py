from typing import Dict

from journeys.config import Config
from journeys.modifier.conflict.plugins.Plugin import FIELD_VALUE_NOT_SUPPORTED
from journeys.modifier.conflict.plugins.Plugin import Plugin
from journeys.modifier.conflict.plugins.Plugin import find_objects_with_field_value
from journeys.modifier.dependency import DependencyMap


class SPDAG(Plugin):
    ID: str = "SPDAG"
    MSG_TYPE: str = FIELD_VALUE_NOT_SUPPORTED
    MSG_INFO: str = "cmp hash"

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
            find_objects_with_field_value(
                config=config,
                type_matcher=("net", "vlan"),
                field_name="cmp-hash",
                field_value=["src-ip", "dst-ip"],
            ),
            as3_declaration=as3_declaration,
            as3_file_name=as3_file_name,
        )

    def change_value_to_default(
        self, mutable_config: Config, mutable_as3_declaration: Dict
    ):
        for obj_id in self.objects:
            obj = mutable_config.fields.get(obj_id)
            field = obj.fields["cmp-hash"]
            field.value = "default"

    def mitigations(self):
        return {
            "comment_only": self.comment_objects,
            "recommended": self.change_value_to_default,
            "mitigations": {
                "delete_objects": self.delete_objects,
                "change_value_to_default": self.change_value_to_default,
            },
        }
