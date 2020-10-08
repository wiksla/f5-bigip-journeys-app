from collections import defaultdict
from itertools import chain
from itertools import product
from typing import Iterable
from typing import List
from typing import Set
from typing import Tuple
from typing import Union

from journeys.config import Config
from journeys.modifier.conflict.plugins.Plugin import TYPE_NOT_SUPPORTED
from journeys.modifier.conflict.plugins.Plugin import Plugin
from journeys.modifier.conflict.plugins.Plugin import find_object_with_type_match
from journeys.modifier.conflict.plugins.Plugin import find_objects_with_field_value
from journeys.modifier.conflict.plugins.Plugin import generate_dependency_comments
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
    MSG_TYPE_2: str = "{}: Not supported command in iRule object"
    MSG_TYPE_3: str = "{}: pem module in not supported"

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

        self.irules = self.check_irules_status(config)

        super().__init__(
            config, dependency_map, self.pem | self.provision | self.irules,
        )

    def check_irules_status(self, mutable_config: Config):
        irules_not_processed = set()

        for obj in self.irules:
            obj_irule = mutable_config.fields.get(obj)
            index = (
                int(obj_irule.parent.index(obj_irule)) - 1
            )  # First object above iRule
            for x in range(index, 1, -1):
                try:
                    obj_comment = mutable_config.fields.get(x)
                    comment = obj_comment.data["comment"]

                    if self.MSG_TYPE_2.format("") in comment:
                        break  # Already processed
                except KeyError:
                    irules_not_processed.add(obj)
                    break  # No comments

        return irules_not_processed

    def comment_objects(self, mutable_config: Config, only_irules=False):
        comments = defaultdict(list)

        for obj_id in self.irules:
            comments[obj_id].append(self.MSG_TYPE_2.format(self.ID))

        if not only_irules:
            for obj_id in self.pem:
                comments[obj_id].append(self.MSG_TYPE_1.format(self.ID, self.MSG_INFO))

            for obj_id in self.provision:
                comments[obj_id].append(self.MSG_TYPE_3.format(self.ID))

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

    def delete_objects(self, mutable_config: Config):
        for obj_id in self.pem:
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
        self.comment_objects(mutable_config=mutable_config, only_irules=True)

    def mitigations(self):
        return {
            "comment_only": self.comment_objects,
            "recommended": self.adjust_objects,
            "mitigations": {"adjust_objects": self.adjust_objects},
        }

    def summary(self) -> List:
        summary = []

        for msg, obj_id, field_name in chain(
            product([self.MSG_TYPE_1], self.pem, [self.MSG_INFO]),
            product([self.MSG_TYPE_2], self.irules, [""]),
            product([self.MSG_TYPE_3], self.provision, [""]),
        ):
            summary.append(msg.format(obj_id, field_name))

        return summary
