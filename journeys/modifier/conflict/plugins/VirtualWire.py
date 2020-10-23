from itertools import chain
from itertools import product
from typing import Dict

from journeys.config import Config
from journeys.modifier.conflict.plugins.Plugin import FIELD_VALUE_NOT_SUPPORTED
from journeys.modifier.conflict.plugins.Plugin import Plugin
from journeys.modifier.conflict.plugins.Plugin import find_objects_with_field_value
from journeys.modifier.dependency import DependencyMap


class VirtualWire(Plugin):
    ID: str = "VirtualWire"
    MSG_TYPE: str = FIELD_VALUE_NOT_SUPPORTED

    def __init__(
        self,
        config: Config,
        dependency_map: DependencyMap,
        as3_declaration: Dict,
        as3_file_name: str,
    ):

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

        self.virtwire_tagged_vlans = find_objects_with_field_value(
            config=config,
            type_matcher=("net", "vlan"),
            field_name="tag",
            field_value="4096",
        )

        # skip duplicates
        self.virtwire_tagged_vlans -= self.vlans

        self.interfaces = find_objects_with_field_value(
            config=config,
            type_matcher=("net", "interface"),
            field_name="port-fwd-mode",
            field_value="virtual-wire",
        )

        super().__init__(
            config,
            dependency_map,
            self.vlan_groups
            | self.vlans
            | self.interfaces
            | self.virtwire_tagged_vlans,
            as3_declaration=as3_declaration,
            as3_file_name=as3_file_name,
        )

    def generate_object_info(self) -> dict:
        object_info = {}

        for obj_id, field_name in chain(
            product(self.vlan_groups, ["mode"]),
            product(self.vlans, ["fwd-mode"]),
            product(self.interfaces, ["port-fwd-mode"]),
        ):
            obj = self.config.fields.get(obj_id)
            object_info[obj_id] = {
                "file": obj.file,
                "comment": self.MSG_TYPE.format(field_name),
                "object": str(obj),
            }

        for obj_id in self.virtwire_tagged_vlans:
            object_info[obj_id] = {
                "file": obj.file,
                "comment": "Object uses a virtual-wire specific tag.",
                "object": str(self.config.fields.get(obj_id)).splitlines(),
            }

        return object_info
