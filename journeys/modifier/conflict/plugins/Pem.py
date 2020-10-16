from itertools import chain
from itertools import product
from typing import Iterable
from typing import Set
from typing import Tuple
from typing import Union

from journeys.config import Config
from journeys.modifier.conflict.plugins.Plugin import TYPE_NOT_SUPPORTED
from journeys.modifier.conflict.plugins.Plugin import Plugin
from journeys.modifier.conflict.plugins.Plugin import find_object_with_type_match
from journeys.modifier.conflict.plugins.Plugin import find_objects_with_field_value
from journeys.modifier.dependency import DependencyMap


def find_objects_with_string_in_key(
    config: Config,
    type_matcher: Tuple[str, ...],
    string_matcher: Union[str, Iterable[str]],
) -> Set[str]:

    objects = set()

    if isinstance(string_matcher, str):
        string_matcher = [string_matcher]

    for obj_ in config.fields.get_all(type_matcher):
        for field in obj_.fields:
            if any(x in field.key for x in string_matcher):
                objects.add(obj_.id)

    return objects


class Pem(Plugin):
    ID: str = "PEM"
    MSG_INFO: str = "pem"

    IRULES_CMDS = ["CLASSIFICATION::", "CLASSIFY::", "PEM::", "PSC::"]

    MSG_TYPE_1: str = TYPE_NOT_SUPPORTED
    MSG_TYPE_2: str = "Unsupported command in iRule object"
    MSG_TYPE_3: str = "Pem module is not supported"

    def __init__(self, config: Config, dependency_map: DependencyMap):
        self.pem = find_object_with_type_match(config=config, type_matcher=("pem",))
        self.irules = find_objects_with_string_in_key(
            config=config, type_matcher=("ltm", "rule"), string_matcher=self.IRULES_CMDS
        )
        self.provision = find_objects_with_field_value(
            config=config,
            type_matcher=("sys", "provision", "pem"),
            field_name="level",
            field_value=["nominal", "minimum", "dedicated", "custom"],
        )

        conflict_objects = None

        # each conf can have a few empty fields which don't mean that pem is enabled
        # ignore the conflict if that is the case
        if not self.provision and not self.irules:
            ignored = {
                "pem global-settings gx",
                "pem global-settings analytics",
                "pem global-settings policy",
            }
            for obj in self.pem:
                if obj not in ignored or len(config.fields[obj].fields) != 0:
                    break
            else:
                conflict_objects = set()

        if conflict_objects is None:
            conflict_objects = self.pem | self.provision | self.irules

        super().__init__(
            config, dependency_map, conflict_objects,
        )

    def delete_objects(self, mutable_config: Config):
        for obj_id in self.pem | self.irules:
            obj = mutable_config.fields.get(obj_id)
            obj.delete()
            if obj_id in self.dependency_map.reverse:
                for related_id in self.dependency_map.reverse[obj_id]:
                    self.dependency_map.apply_resolution(
                        mutable_config, related_id, obj_id
                    )

    def modify_objects(self, mutable_config: Config):
        for obj_id in self.provision:
            obj = mutable_config.fields.get(obj_id)
            field = obj.fields["level"]
            field.value = "none"

    def adjust_objects(self, mutable_config: Config):
        self.delete_objects(mutable_config)
        self.modify_objects(mutable_config)

    def mitigations(self):
        return {
            "comment_only": self.comment_objects,
            "recommended": self.adjust_objects,
            "mitigations": {"adjust_objects": self.adjust_objects},
        }

    def generate_object_info(self) -> dict:
        object_info = {}

        for msg, obj_id, field_name in chain(
            product([self.MSG_TYPE_1], self.pem, [self.MSG_INFO]),
            product([self.MSG_TYPE_2], self.irules, [""]),
            product([self.MSG_TYPE_3], self.provision, [""]),
        ):
            obj = self.config.fields.get(obj_id)
            object_info[obj_id] = {
                "file": obj.file,
                "comment": msg.format(field_name),
                "object": str(obj),
            }

        return object_info
