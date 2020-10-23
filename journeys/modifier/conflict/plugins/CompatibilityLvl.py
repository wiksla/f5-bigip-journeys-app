import configparser
from typing import Dict

from journeys.config import Config
from journeys.modifier.conflict.plugins.Plugin import FIELD_VALUE_NOT_SUPPORTED
from journeys.modifier.conflict.plugins.Plugin import Plugin
from journeys.modifier.conflict.plugins.Plugin import find_objects_with_field_value
from journeys.modifier.dependency import DependencyMap


class CompatibilityLevel(Plugin):
    ID: str = "CompatibilityLevel"
    MSG_TYPE: str = FIELD_VALUE_NOT_SUPPORTED
    MSG_INFO: str = "level"

    def __init__(
        self,
        config: Config,
        dependency_map: DependencyMap,
        as3_declaration: Dict,
        as3_file_name: str,
    ):
        self.compatibility_lvl_is_2 = find_objects_with_field_value(
            config=config,
            type_matcher=("sys", "compatibility-level"),
            field_name="level",
            field_value="2",
        )

        self.compatibility_lvl_is_1 = find_objects_with_field_value(
            config=config,
            type_matcher=("sys", "compatibility-level"),
            field_name="level",
            field_value="1",
        )

        if self.compatibility_lvl_is_1 and self._check_if_dos_forcewdos_was_enabled(
            config=config
        ):
            self.compatibility_lvl_is_1 = set()

        super().__init__(
            config=config,
            dependency_map=dependency_map,
            objects=self.compatibility_lvl_is_1 or self.compatibility_lvl_is_2,
            as3_declaration=as3_declaration,
            as3_file_name=as3_file_name,
        )

    @staticmethod
    def _check_if_dos_forcewdos_was_enabled(config):
        try:
            return config.bigdb.get(section="Dos.ForceSWdos", option="value") == "true"
        except configparser.NoOptionError:
            return False

    def render_files(self):
        files_to_render = super().render_files()
        files_to_render.add(self.config.bigdb.FILENAME)
        return files_to_render

    def set_compatibility_lvl_to_0(
        self, mutable_config: Config, mutable_as3_declaration: Dict
    ):
        level = self._find_level_field(mutable_config=mutable_config)
        level.value = "0"

    def set_compatibility_lvl_to_1(
        self, mutable_config: Config, mutable_as3_declaration: Dict
    ):
        level = self._find_level_field(mutable_config=mutable_config)
        level.value = "1"
        mutable_config.bigdb.set(section="Dos.ForceSWdos", option="value", value="true")

    def _find_level_field(self, mutable_config: Config):
        for obj_id in self.objects:
            obj = mutable_config.fields.get(obj_id)
            return obj.fields["level"]

    def comment_objects(self, mutable_config: Config, mutable_as3_declaration: Dict):
        if self.compatibility_lvl_is_1:
            CompatibilityLevel.MSG_TYPE = (
                "{}: sys compatibility {} 1 require [Dos.ForceSWdos] "
                "'value' set to 'true' (BigDB.dat)."
            )
        super().comment_objects(
            mutable_config=mutable_config,
            mutable_as3_declaration=mutable_as3_declaration,
        )

    def mitigations(self) -> dict:
        return {
            "comment_only": self.comment_objects,
            "recommended": self.set_compatibility_lvl_to_1,
            "mitigations": {
                "compatibility_lvl_0": self.set_compatibility_lvl_to_0,
                "compatibility_lvl_1": self.set_compatibility_lvl_to_1,
            },
        }
