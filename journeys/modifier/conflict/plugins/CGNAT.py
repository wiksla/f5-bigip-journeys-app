from typing import Set
from typing import Tuple

from journeys.config import Config
from journeys.modifier.conflict.plugins.Plugin import TYPE_NOT_SUPPORTED
from journeys.modifier.conflict.plugins.Plugin import Plugin
from journeys.modifier.conflict.plugins.Plugin import find_object_with_type_match
from journeys.modifier.conflict.plugins.Plugin import find_objects_with_field_name
from journeys.modifier.dependency import DependencyMap


# TODO: consider refactor/optimize searching mechanism in config for nested structure
def find_nested_field_value(
    config: Config, type_matcher: Tuple[str, ...], field_name: str, field_value: str
) -> Set[str]:
    objects = set()

    def flatten(top_level_field):
        for field_ in top_level_field.fields:
            if field_.fields:
                yield from flatten(field_)
            else:
                yield field_

    for top_lvl_field in config.fields.get_all(type_matcher):
        for specific_field in flatten(top_level_field=top_lvl_field):
            if specific_field.key == field_name and specific_field.value == field_value:
                objects.add(top_lvl_field.id)

    return objects


class CGNAT(Plugin):
    ID: str = "CGNAT"
    MSG_INFO: str = "cgnat"

    MSG_TYPE: str = TYPE_NOT_SUPPORTED

    def __init__(self, config: Config, dependency_map: DependencyMap):

        self.cgnat_enabled = find_objects_with_field_name(
            config=config,
            type_matcher=("sys", "feature-module", "cgnat"),
            field_name="enabled",
        )

        self.lsn_pools = find_object_with_type_match(
            config=config, type_matcher=("ltm", "lsn-pool")
        )

        self.ltm_profile_pcp = find_object_with_type_match(
            config=config, type_matcher=("ltm", "profile", "pcp")
        )

        self.ltm_virtual_pool_type_lsn = find_nested_field_value(
            config=config,
            type_matcher=("ltm", "virtual"),
            field_name="type",
            field_value="lsn",
        )

        super().__init__(
            config=config,
            dependency_map=dependency_map,
            objects=self.cgnat_enabled
            | self.lsn_pools
            | self.ltm_profile_pcp
            | self.ltm_virtual_pool_type_lsn,
        )
