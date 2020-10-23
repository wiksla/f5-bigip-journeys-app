import configparser
import logging
from typing import Dict

from journeys.config import Config
from journeys.modifier.conflict.plugins.Plugin import FIELD_NOT_SUPPORTED
from journeys.modifier.conflict.plugins.Plugin import Plugin
from journeys.modifier.conflict.plugins.Plugin import find_objects_with_field_name
from journeys.modifier.conflict.plugins.Plugin import find_objects_with_field_value
from journeys.modifier.dependency import DependencyMap

log = logging.getLogger(__name__)


class SPVA(Plugin):
    ID: str = "SPVA"
    MSG_TYPE: str = FIELD_NOT_SUPPORTED
    MSG_INFO: str = "address-list"

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
            field_name="address-list",
        )

        self.compatibility_lvl_is_1 = find_objects_with_field_value(
            config=config,
            type_matcher=("sys", "compatibility-level"),
            field_name="level",
            field_value="1",
        )

        self.compatibility_lvl = find_objects_with_field_name(
            config=config,
            type_matcher=("sys", "compatibility-level"),
            field_name="level",
        )

        if self.compatibility_lvl_is_1 and self._check_if_dos_forcewdos_was_enabled(
            config=config
        ):
            self.to_check = set()
        else:
            self.to_check = self.to_remove

        super().__init__(
            config,
            dependency_map,
            self.to_check,
            as3_declaration=as3_declaration,
            as3_file_name=as3_file_name,
        )

    @staticmethod
    def _check_if_dos_forcewdos_was_enabled(config):
        try:
            return config.bigdb.get(section="Dos.ForceSWdos", option="value") == "true"
        except configparser.NoOptionError:
            return False

    def build_dependencies(self):
        for obj_id in self.objects:
            dependencies = self.dependency_map.get_dependencies(obj_id=obj_id)
            log.debug(f"Plugin: {self.ID} | Object: {obj_id}  | {dependencies}")
            self.dependencies.update(dependencies)

    def render_files(self):
        files_to_render = super().render_files()
        files_to_render.add(self.config.bigdb.FILENAME)
        return files_to_render

    def delete_objects(self, mutable_config: Config, mutable_as3_declaration: Dict):
        for obj_id in self.all_objects:
            obj = mutable_config.fields.get(obj_id)
            for field in obj.fields:
                if field.key == "address-list":
                    field.delete()
                    break
            else:
                obj.delete()

        self.set_compatibility_lvl(mutable_config=mutable_config, value="0")

    def comment_objects(self, mutable_config: Config, mutable_as3_declaration: Dict):
        super().comment_objects(
            mutable_config=mutable_config,
            mutable_as3_declaration=mutable_as3_declaration,
            dependency=False,
        )

    def set_compatibility_lvl(self, mutable_config: Config, value):
        level = self._find_level_field(mutable_config=mutable_config)
        level.value = value

    def compatibility_lvl_to_1(
        self, mutable_config: Config, mutable_as3_declaration: Dict
    ):
        self.set_compatibility_lvl(mutable_config=mutable_config, value="1")
        mutable_config.bigdb.set(section="Dos.ForceSWdos", option="value", value="true")

    def _find_level_field(self, mutable_config: Config):
        for obj_id in self.compatibility_lvl:
            obj = mutable_config.fields.get(obj_id)
            return obj.fields["level"]

    def mitigations(self):
        return {
            "comment_only": self.comment_objects,
            "recommended": self.compatibility_lvl_to_1,
            "mitigations": {
                "delete_objects": self.delete_objects,
                "compatibility_lvl_1": self.compatibility_lvl_to_1,
            },
        }
