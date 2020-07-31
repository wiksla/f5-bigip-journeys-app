from copy import deepcopy
from typing import Callable
from typing import List
from typing import Optional

from journeys.config import Config
from journeys.modifier.conflict.conflict import Conflict
from journeys.modifier.conflict.conflict_plugin import (
    service_provider_DAG_conflict_plugin,
)
from journeys.modifier.conflict.conflict_plugin import virtual_wire_conflict_plugin
from journeys.modifier.dependency import DependencyMap
from journeys.modifier.dependency import build_dependency_map


class ConflictHandler:
    plugins: List[Callable[[Config, DependencyMap], Optional[Conflict]]]

    def __init__(self, config: Config):
        self.config = config
        self.dependency_map = build_dependency_map(self.config)
        self.plugins = [
            service_provider_DAG_conflict_plugin,
            virtual_wire_conflict_plugin,
        ]

    def detect_conflicts(self):
        conflicts = {}
        for plugin in self.plugins:
            conflict = plugin(self.config, self.dependency_map)
            if conflict:
                conflicts[conflict.id] = conflict

        return conflicts

    def render(self, dirname: str, conflict: Conflict, mitigation: str):

        mitigation_func = conflict.mitigations[mitigation]

        config_copy: Config = deepcopy(self.config)
        mitigation_func(config_copy)
        config_copy.build(dirname=dirname, files=conflict.files_to_render)
