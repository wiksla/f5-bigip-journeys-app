import os
from copy import deepcopy
from typing import Callable
from typing import Dict
from typing import List
from typing import Optional
from typing import Type

from journeys.config import Config
from journeys.errors import UnknownConflictError
from journeys.modifier.conflict.as3ucs import As3ucs
from journeys.modifier.conflict.conflict import Conflict
from journeys.modifier.conflict.plugins import load_plugins
from journeys.modifier.conflict.plugins.Plugin import Plugin
from journeys.modifier.dependency import DependencyMap
from journeys.utils.as3_ops import save_declaration


class ConflictHandler:
    plugins: List[Type[Plugin]]

    def __init__(self, config: Config, as3_declaration: Dict, as3_ucs_path: str):
        self.config = config
        self.as3_declaration = as3_declaration
        self.as3_ucs_path = as3_ucs_path
        self.dependency_map = DependencyMap(self.config)
        self.plugins = load_plugins()
        self.as3_declaration_pointer = self.as3_declaration
        if (
            self.as3_declaration_pointer
            and "declaration" in self.as3_declaration_pointer
        ):
            self.as3_declaration_pointer = self.as3_declaration_pointer["declaration"]

    def get_conflicts(self) -> dict:
        conflicts = {}
        for plugin in self.plugins:
            conflict = plugin(
                config=self.config,
                dependency_map=self.dependency_map,
                as3_declaration=self.as3_declaration_pointer,
                as3_file_name=os.path.basename(self.as3_ucs_path)
                if self.as3_ucs_path
                else None,
            ).get_conflict()

            if conflict:
                conflicts[conflict.id] = conflict

        return conflicts

    def get_conflict(self, conflict_id: str) -> Conflict:
        conflicts = self.get_conflicts()
        try:
            return conflicts[conflict_id]
        except KeyError:
            raise UnknownConflictError(conflict_id=conflict_id)

    def render(
        self,
        dirname,
        conflict: Optional[Conflict] = None,
        mitigation_func: Optional[Callable] = None,
    ):
        if not conflict:
            self.config.build(dirname=dirname)
            if self.as3_ucs_path:
                save_declaration(self.as3_declaration, self.as3_ucs_path)
            return

        assert mitigation_func is not None

        config_copy: Config = deepcopy(self.config)
        as3_declaration_copy = deepcopy(self.as3_declaration)
        mitigation_func(
            mutable_config=config_copy, mutable_as3_declaration=as3_declaration_copy
        )
        config_copy.build(dirname=dirname, files=conflict.files_to_render)
        if self.as3_ucs_path:
            as3_ucs = As3ucs(declaration=as3_declaration_copy)
            as3_ucs.process_ucs_changes(config_copy)
            save_declaration(as3_declaration_copy, self.as3_ucs_path)
