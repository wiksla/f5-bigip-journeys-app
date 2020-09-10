from collections import defaultdict
from typing import Dict
from typing import Iterable
from typing import List
from typing import Set
from typing import Tuple
from typing import Union

from journeys.config import Config
from journeys.config import Field
from journeys.modifier.conflict.conflict import Conflict
from journeys.modifier.dependency import DependencyMap

FIELD_VALUE_NOT_SUPPORTED: str = "{}: Value of field {} is not supported on target platform"
FIELD_NOT_SUPPORTED: str = "{}: Field {} is not supported on target platform"
TYPE_NOT_SUPPORTED: str = "{}: Type {} is not supported on target platform"


def generate_dependency_comments(
    conflict_id: str,
    dependency_map: DependencyMap,
    obj_id: Union[str, Iterable[str]],
    comments: Dict[str, List[str]],
):

    obj_ids = [obj_id] if isinstance(obj_id, str) else obj_id

    for obj_id in obj_ids:

        def generate_comment(parent: str, child: str):
            comment = "{}: Depends on an object '{}' which requires an action".format(
                conflict_id, parent
            )
            if comment not in comments[child]:
                comments[child].append(comment)

        dependency_map.dfs(
            func=generate_comment, _map=dependency_map.reverse, obj_id=obj_id
        )


def find_objects_with_field_value(
    config: Config,
    type_matcher: Tuple[str, ...],
    field_name: str,
    field_value: Union[str, Iterable[str]],
) -> Set[str]:
    objects = set()

    if isinstance(field_value, str):
        field_value = [field_value]

    obj: Field
    for obj in config.fields.get_all(type_matcher):
        try:
            if obj.fields[field_name].value in field_value:
                objects.add(obj.id)
        except KeyError:
            continue

    return objects


def find_objects_with_field_name(
    config: Config, type_matcher: Tuple[str, ...], field_name: str,
) -> Set[str]:

    objects = set()

    for obj_ in config.fields.get_all(type_matcher):
        try:
            _ = obj_.fields[field_name]
            objects.add(obj_.id)
        except KeyError:
            continue
    return objects


def find_object_with_type_match(
    config: Config, type_matcher: Tuple[str, ...]
) -> Set[str]:
    objects = set()
    for obj_ in config.fields.get_all(type_matcher):
        objects.add(obj_.id)
    return objects


class Plugin:
    ID: str = None
    MSG_TYPE: str = None
    MSG_INFO: str = None

    def __init__(
        self, config: Config, dependency_map: DependencyMap, objects: Set,
    ):
        self.dependency_map = dependency_map
        self.config = config

        self.objects = objects
        self.dependencies = set()
        self.build_dependencies()
        self.all_objects = self.objects | self.dependencies

    def build_dependencies(self):
        for obj_id in self.objects:
            self.dependencies.update(self.dependency_map.get_dependents(obj_id=obj_id))

    def render_files(self):
        files_to_render = set()
        for obj_id in self.all_objects:
            obj = self.config.fields.get(obj_id)
            files_to_render.add(obj.file)
        return files_to_render

    def comment_objects(self, mutable_config: Config, dependency=True):
        comments = defaultdict(list)

        for obj_id in self.objects:
            comments[obj_id].append(self.MSG_TYPE.format(self.ID, self.MSG_INFO))

        if dependency:
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

    def summary(self) -> List:
        return [self.MSG_TYPE.format(obj_id, self.MSG_INFO) for obj_id in self.objects]

    def delete_objects(self, mutable_config: Config):
        for obj_id in self.objects:
            obj = mutable_config.fields.get(obj_id)
            obj.delete()
            if obj_id in self.dependency_map.reverse:
                for related_id in self.dependency_map.reverse[obj_id]:
                    self.dependency_map.resolutions[(related_id, obj_id)](
                        mutable_config
                    )

    def get_conflict(self) -> Conflict:
        if not self.objects:
            return None
        return Conflict(
            id=self.ID,
            summary=self.summary(),
            files_to_render=self.render_files(),
            mitigations=self.mitigations(),
        )

    def mitigations(self) -> dict:
        return {
            "comment_only": self.comment_objects,
            "delete_objects": self.delete_objects,
        }
