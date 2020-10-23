from itertools import chain
from itertools import product
from typing import Dict

from journeys.config import Config
from journeys.modifier.conflict.plugins.Plugin import FIELD_NOT_SUPPORTED
from journeys.modifier.conflict.plugins.Plugin import FIELD_VALUE_NOT_SUPPORTED
from journeys.modifier.conflict.plugins.Plugin import Plugin
from journeys.modifier.conflict.plugins.Plugin import find_objects_with_field_name
from journeys.modifier.conflict.plugins.Plugin import find_objects_with_field_value
from journeys.modifier.dependency import DependencyMap


class WildcardWhitelist(Plugin):
    ID: str = "WildcardWhitelist"
    MSG_TYPE_1: str = FIELD_NOT_SUPPORTED
    MSG_TYPE_2: str = FIELD_VALUE_NOT_SUPPORTED

    def __init__(
        self,
        config: Config,
        dependency_map: DependencyMap,
        as3_declaration: Dict,
        as3_file_name: str,
    ):
        self.to_remove = find_objects_with_field_name(
            config=config,
            type_matcher=("security", "dos", "network-whitelist"),
            field_name="extended-entries",
        )
        self.to_change = find_objects_with_field_value(
            config=config,
            type_matcher=("sys", "compatibility-level"),
            field_name="level",
            field_value="2",
        )

        super().__init__(
            config,
            dependency_map,
            self.to_remove | self.to_change,
            as3_declaration=as3_declaration,
            as3_file_name=as3_file_name,
        )

    def change_value_to_default(self, mutable_config: Config):
        for obj_id in self.to_change:
            obj = mutable_config.fields.get(obj_id)
            field = obj.fields["level"]
            field.value = "0"

    def delete_objects(self, mutable_config: Config, mutable_as3_declaration: Dict):
        for obj_id in self.to_remove:
            obj = mutable_config.fields.get(obj_id)
            obj.delete()

    def adjust_objects(self, mutable_config: Config, mutable_as3_declaration: Dict):
        self.delete_objects(
            mutable_config=mutable_config,
            mutable_as3_declaration=mutable_as3_declaration,
        )
        self.change_value_to_default(mutable_config=mutable_config)

    def mitigations(self):
        return {
            "comment_only": self.comment_objects,
            "recommended": self.adjust_objects,
            "mitigations": {"adjust_objects": self.adjust_objects},
        }

    def generate_object_info(self) -> dict:
        object_info = {}

        for msg, obj_id, field_name in chain(
            product([self.MSG_TYPE_1], self.to_remove, ["extended-entries"]),
            product([self.MSG_TYPE_2], self.to_change, ["level"]),
        ):
            obj = self.config.fields.get(obj_id)
            object_info[obj_id] = {
                "file": obj.file,
                "comment": msg.format(field_name),
                "object": str(obj),
            }
        return object_info
