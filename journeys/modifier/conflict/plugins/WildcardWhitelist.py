from collections import defaultdict
from itertools import chain
from itertools import product
from typing import List

from journeys.config import Config
from journeys.modifier.conflict.plugins.Plugin import FIELD_NOT_SUPPORTED
from journeys.modifier.conflict.plugins.Plugin import FIELD_VALUE_NOT_SUPPORTED
from journeys.modifier.conflict.plugins.Plugin import Plugin
from journeys.modifier.conflict.plugins.Plugin import find_objects_with_field_name
from journeys.modifier.conflict.plugins.Plugin import find_objects_with_field_value
from journeys.modifier.conflict.plugins.Plugin import generate_dependency_comments
from journeys.modifier.dependency import DependencyMap


class WildcardWhitelist(Plugin):
    ID: str = "WildcardWhitelist"
    MSG_TYPE_1: str = FIELD_NOT_SUPPORTED
    MSG_TYPE_2: str = FIELD_VALUE_NOT_SUPPORTED

    def __init__(self, config: Config, dependency_map: DependencyMap):
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

        super().__init__(config, dependency_map, self.to_remove | self.to_change)

    def comment_objects(self, mutable_config: Config):

        comments = defaultdict(list)

        for msg, obj_id, field_name in chain(
            product([self.MSG_TYPE_1], self.to_remove, ["extended-entries"]),
            product([self.MSG_TYPE_2], self.to_change, ["level"]),
        ):
            comments[obj_id].append(msg.format(self.ID, field_name))

        generate_dependency_comments(
            conflict_id=self.ID,
            dependency_map=self.dependency_map,
            obj_id=self.all_objects,
            comments=comments,
        )

        for obj_id, comment_list in comments.items():
            obj = mutable_config.fields.get(obj_id)
            for comment in comment_list:
                obj.insert_before(args=["#"]).data["comment"] = comment

    def change_value_to_default(self, mutable_config: Config):
        for obj_id in self.to_change:
            obj = mutable_config.fields.get(obj_id)
            field = obj.fields["level"]
            field.value = "0"

    def delete_objects(self, mutable_config: Config):
        for obj_id in self.to_remove:
            obj = mutable_config.fields.get(obj_id)
            obj.delete()

    def adjust_objects(self, mutable_config: Config):
        self.delete_objects(mutable_config)
        self.change_value_to_default(mutable_config)

    def mitigations(self):
        return {
            "comment_only": self.comment_objects,
            "recommended": self.adjust_objects,
            "mitigations": {"adjust_objects": self.adjust_objects},
        }

    def summary(self) -> List:
        summary = []

        for msg, obj_id, field_name in chain(
            product([self.MSG_TYPE_1], self.to_remove, ["extended-entries"]),
            product([self.MSG_TYPE_2], self.to_change, ["level"]),
        ):
            summary.append(msg.format(obj_id, field_name))

        return summary
