from collections import defaultdict
from itertools import chain
from itertools import product
from typing import List

from journeys.config import Config
from journeys.modifier.conflict.plugins.Plugin import FIELD_VALUE_NOT_SUPPORTED
from journeys.modifier.conflict.plugins.Plugin import Plugin
from journeys.modifier.conflict.plugins.Plugin import find_objects_with_field_value
from journeys.modifier.conflict.plugins.Plugin import generate_dependency_comments
from journeys.modifier.dependency import DependencyMap


class VirtualWire(Plugin):
    ID: str = "VirtualWire"
    MSG_TYPE: str = FIELD_VALUE_NOT_SUPPORTED

    def __init__(self, config: Config, dependency_map: DependencyMap):

        self.vlan_groups = find_objects_with_field_value(
            config=config,
            type_matcher=("net", "vlan-group"),
            field_name="mode",
            field_value="virtual-wire",
        )

        self.vlans = find_objects_with_field_value(
            config=config,
            type_matcher=("net", "vlan"),
            field_name="fwd-mode",
            field_value="virtual-wire",
        )

        self.interfaces = find_objects_with_field_value(
            config=config,
            type_matcher=("net", "interface"),
            field_name="port-fwd-mode",
            field_value="virtual-wire",
        )

        super().__init__(
            config, dependency_map, self.vlan_groups | self.vlans | self.interfaces
        )

    def summary(self) -> List:
        summary = []

        for obj_id, field_name in chain(
            product(self.vlan_groups, ["mode"]),
            product(self.vlans, ["fwd-mode"]),
            product(self.interfaces, ["port-fwd-mode"]),
        ):
            summary.append(self.MSG_TYPE.format(obj_id, field_name))

        return summary

    def comment_objects(self, mutable_config: Config):

        comments = defaultdict(list)

        for obj_id, field_name in chain(
            product(self.vlan_groups, ["mode"]),
            product(self.vlans, ["fwd-mode"]),
            product(self.interfaces, ["port-fwd-mode"]),
        ):
            comments[obj_id].append(self.MSG_TYPE.format(self.ID, field_name))

        generate_dependency_comments(
            conflict_id=self.ID,
            dependency_map=self.dependency_map,
            obj_id=self.objects,
            comments=comments,
        )

        for obj_id, comment_list in comments.items():
            obj = mutable_config.fields.get(obj_id)
            for comment in comment_list:
                obj.insert_before(args=["#"]).data["comment"] = comment
