from copy import deepcopy
from typing import List
from typing import Type

from journeys.config import Config
from journeys.errors import UnknownConflictError
from journeys.modifier.conflict.conflict import Conflict
from journeys.modifier.conflict.plugins import load_plugins
from journeys.modifier.conflict.plugins.Plugin import Plugin
from journeys.modifier.dependency import DependencyMap


class ConflictHandler:
    plugins: List[Type[Plugin]]

    def __init__(self, config: Config):
        self.config = config
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

    def render(self, dirname: str, conflict: Conflict, mitigation: str):
        mitigation_func = conflict.mitigations[mitigation]
        config_copy: Config = deepcopy(self.config)
        mitigation_func(config_copy)
        config_copy.build(dirname=dirname, files=conflict.files_to_render)
