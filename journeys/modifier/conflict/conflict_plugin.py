from collections import defaultdict
from typing import Dict
from typing import Iterable
from typing import List
from typing import Optional
from typing import Set
from typing import Tuple
from typing import Union

from journeys.config import Config
from journeys.config import Field
from journeys.modifier.conflict.conflict import Conflict
from journeys.modifier.dependency import DependencyMap

FIELD_VALUE_NOT_SUPPORTED: str = "{}: Value of field {} is not supported on target platform"


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


def service_provider_DAG_conflict_plugin(
    config: Config, dependency_map: DependencyMap
) -> Optional[Conflict]:
    """
    Function to detect and mitigate "Service Provider DAG" conflict

    Details:
    https://cxt.pages.gitswarm.f5net.com/journeys/docs/journeys_documentation/migration_tool/flagging_unsupported_objects/service_provider_dag/service_provider_dag.html
    """

    conflict_id = "SPDAG"

    objects = find_objects_with_field_value(
        config=config,
        type_matcher=("net", "vlan"),
        field_name="cmp-hash",
        field_value=["src-ip", "dst-ip"],
    )

    if not objects:
        return None

    dependencies = set()
    for obj_id in objects:
        dependencies.update(dependency_map.get_dependents(obj_id=obj_id))

    summary = [
        FIELD_VALUE_NOT_SUPPORTED.format(obj_id, "cmp-hash") for obj_id in objects
    ]

    all_objects = objects | dependencies

    files_to_render = set()
    for obj_id in all_objects:
        obj = config.fields.get(obj_id)
        files_to_render.add(obj.file)

    def comment_objects(mutable_config: Config):

        comments = defaultdict(list)

        for obj_id in objects:
            comments[obj_id].append(
                FIELD_VALUE_NOT_SUPPORTED.format(conflict_id, "cmp-hash")
            )

        generate_dependency_comments(
            conflict_id=conflict_id,
            dependency_map=dependency_map,
            obj_id=objects,
            comments=comments,
        )

        for obj_id, comment_list in comments.items():
            obj = mutable_config.fields.get(obj_id)
            for comment in comment_list:
                obj.insert_before(args=["#"]).data["comment"] = comment

    def change_value_to_default(mutable_config: Config):
        for obj_id in objects:
            obj = mutable_config.fields.get(obj_id)
            field = obj.fields["cmp-hash"]
            field.value = "default"

    def delete_objects(mutable_config: Config):
        for obj_id in all_objects:
            obj = mutable_config.fields.get(obj_id)
            obj.delete()

    return Conflict(
        id=conflict_id,
        summary=summary,
        files_to_render=files_to_render,
        mitigations={
            "base": comment_objects,
            "change_value_to_default": change_value_to_default,
            "delete_objects": delete_objects,
        },
    )


def virtual_wire_conflict_plugin(
    config: Config, dependency_map: DependencyMap
) -> Optional[Conflict]:
    """
    Function to detect and mitigate "Virtual Wire" conflict

    Details:
    https://cxt.pages.gitswarm.f5net.com/journeys/docs/journeys_documentation/migration_tool/flagging_unsupported_objects/virtual_wire/virtual_wire.html
    """

    conflict_id = "VirtualWire"

    vlan_groups = find_objects_with_field_value(
        config=config,
        type_matcher=("net", "vlan-group"),
        field_name="mode",
        field_value="virtual-wire",
    )
    vlans = find_objects_with_field_value(
        config=config,
        type_matcher=("net", "vlan"),
        field_name="fwd-mode",
        field_value="virtual-wire",
    )
    interfaces = find_objects_with_field_value(
        config=config,
        type_matcher=("net", "interface"),
        field_name="port-fwd-mode",
        field_value="virtual-wire",
    )

    objects = vlan_groups | vlans | interfaces

    if not objects:
        return None

    summary = []

    for obj_id in vlan_groups:
        summary.append(FIELD_VALUE_NOT_SUPPORTED.format(obj_id, "mode"))

    for obj_id in vlans:
        summary.append(FIELD_VALUE_NOT_SUPPORTED.format(obj_id, "fwd-mode"))

    for obj_id in interfaces:
        summary.append(FIELD_VALUE_NOT_SUPPORTED.format(obj_id, "port-fwd-mode"))

    dependencies = set()
    for obj_id in objects:
        dependencies.update(dependency_map.get_dependents(obj_id=obj_id))

    all_objects = objects | dependencies

    files_to_render = set()
    for obj_id in all_objects:
        obj = config.fields.get(obj_id)
        files_to_render.add(obj.file)

    def comment_objects(mutable_config: Config):

        comments = defaultdict(list)

        for obj_id in vlan_groups:
            comments[obj_id].append(
                FIELD_VALUE_NOT_SUPPORTED.format(conflict_id, "mode")
            )

        for obj_id in vlans:
            comments[obj_id].append(
                FIELD_VALUE_NOT_SUPPORTED.format(conflict_id, "fwd-mode")
            )

        for obj_id in interfaces:
            comments[obj_id].append(
                FIELD_VALUE_NOT_SUPPORTED.format(conflict_id, "port-fwd-mode")
            )

        generate_dependency_comments(
            conflict_id=conflict_id,
            dependency_map=dependency_map,
            obj_id=objects,
            comments=comments,
        )

        for obj_id, comment_list in comments.items():
            obj = mutable_config.fields.get(obj_id)
            for comment in comment_list:
                obj.insert_before(args=["#"]).data["comment"] = comment

    def delete_objects(mutable_config: Config):
        for obj_id in all_objects:
            obj = mutable_config.fields.get(obj_id)
            obj.delete()

    return Conflict(
        id=conflict_id,
        summary=summary,
        files_to_render=files_to_render,
        mitigations={"base": comment_objects, "delete_objects": delete_objects},
    )
