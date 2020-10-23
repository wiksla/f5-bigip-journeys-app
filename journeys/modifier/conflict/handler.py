from copy import deepcopy
from typing import Callable
from typing import Dict
from typing import List
from typing import Optional
from typing import Type

from journeys.as3ucs.as3ucs import As3ucs
from journeys.config import Config
from journeys.errors import UnknownConflictError
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

    def get_conflicts(self) -> dict:
        conflicts = {}
        for plugin in self.plugins:
            conflict = plugin(self.config, self.dependency_map).get_conflict()

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
        config_copy: Config = deepcopy(self.config)
        as3_declaration_copy = deepcopy(self.as3_declaration)

        if conflict:
            if mitigation_func:
                mitigation_func(config_copy)

        files = conflict.files_to_render if conflict else None
        config_copy.build(dirname=dirname, files=files)

        if self.as3_ucs_path:
            as3_ucs = As3ucs(declaration=as3_declaration_copy)
            as3_ucs.process_ucs_changes(config_copy)
            save_declaration(as3_declaration_copy, self.as3_ucs_path)
