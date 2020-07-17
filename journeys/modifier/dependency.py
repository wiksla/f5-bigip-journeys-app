from collections import defaultdict
from dataclasses import dataclass
from typing import Any
from typing import Callable
from typing import Dict
from typing import List
from typing import Set
from typing import Tuple
from typing import Union

from journeys.config import Config
from journeys.config import Field
from journeys.config import FieldCollection


@dataclass
class FieldDependencyMixIn:
    """Base class for all Field value related dependencies.

    Attributes:
        type_matcher (Tuple[str, ...]): Pattern to use for searching dependency candidates.
    """

    type_matcher: Union[Tuple[str, ...], List[Tuple[str, ...]]]

    def find(self, objects: FieldCollection, obj: Field) -> List[str]:
        """Finds obj dependency among objects.

        Dependency search is done by:
        - retrieving a value from an object
        - finding dependency candidates with use of type_matcher
        - finding a dependency among the candidates by comparing a value retrieved from candidate object
        with value retrieved from object.
        """
        try:
            value = self.get_value(obj=obj)
        except KeyError:
            return []

        ret = []

        if isinstance(self.type_matcher, list):
            type_matcher_list = self.type_matcher
        else:
            type_matcher_list = [self.type_matcher]

        for type_matcher in type_matcher_list:
            for candidate in objects.get_all(type_matcher):
                if self.get_target_value(obj=candidate) == value:
                    ret.append(candidate.id)

        return ret


@dataclass
class FromFieldValueDependencyMixIn:
    field_name: str

    def get_value(self, obj) -> str:
        field = obj.fields[self.field_name]
        return field.value


@dataclass
class FromFieldKeyDependencyMixIn:
    def get_value(self, obj) -> str:
        return obj.key


@dataclass
class FromNameDependencyMixIn:
    def get_value(self, obj) -> str:
        return obj.name


@dataclass
class ToNameDependencyMixIn:
    def get_target_value(self, obj: Field) -> str:
        return obj.name


@dataclass
class ToFieldValueDependencyMixIn:
    target_field_name: str

    def get_target_value(self, obj) -> str:
        return obj.fields[self.target_field_name].value


@dataclass
class FieldValueToNameDependency(
    FromFieldValueDependencyMixIn, ToNameDependencyMixIn, FieldDependencyMixIn
):
    pass


@dataclass
class FieldValueToFieldValueDependency(
    FromFieldValueDependencyMixIn, ToFieldValueDependencyMixIn, FieldDependencyMixIn
):
    pass


@dataclass
class FieldKeyToNameDependency(
    FromFieldKeyDependencyMixIn, ToNameDependencyMixIn, FieldDependencyMixIn
):
    pass


@dataclass
class NameToNameDependency(
    FromNameDependencyMixIn, ToNameDependencyMixIn, FieldDependencyMixIn
):
    pass


@dataclass
class SubCollectionDependency:
    """ Dependency class that allows to find dependencies of each item in a subcollection named field_name

    Attributes:
        field_name (str): name of the field that contains a subcollection of items
        dependency (FieldDependencyMixIn): dependency object to check the subcollection items against
    """

    field_name: str
    dependency: FieldDependencyMixIn

    def find(self, objects: FieldCollection, obj: Field) -> List[str]:

        try:
            members = obj.fields[self.field_name].fields
        except KeyError:
            return []

        ret = []

        for sub_obj in members:
            sub_ret = self.dependency.find(objects, sub_obj)
            if sub_ret:
                ret.extend(sub_ret)

        return ret


monitor_dependency = FieldValueToNameDependency(
    field_name="monitor", type_matcher=("ltm", "monitor")
)

DEPENDENCIES_MATRIX = {
    ("ltm", "pool"): [
        monitor_dependency,
        SubCollectionDependency(field_name="members", dependency=monitor_dependency),
        SubCollectionDependency(
            field_name="members",
            dependency=FieldValueToFieldValueDependency(
                field_name="address",
                type_matcher=("ltm", "node"),
                target_field_name="address",
            ),
        ),
    ],
    ("ltm", "virtual"): [
        SubCollectionDependency(
            field_name="vlans",
            dependency=FieldKeyToNameDependency(
                type_matcher=[("net", "vlan"), ("net", "vlan-group")]
            ),
        )
    ],
    ("net", "vlan-group"): [
        SubCollectionDependency(
            field_name="members",
            dependency=FieldKeyToNameDependency(type_matcher=("net", "vlan")),
        )
    ],
    ("net", "vlan"): [
        NameToNameDependency(type_matcher=("net", "fdb", "vlan")),
        SubCollectionDependency(
            field_name="interfaces",
            dependency=FieldKeyToNameDependency(type_matcher=("net", "trunk")),
        ),
    ],
    ("net", "trunk"): [
        SubCollectionDependency(
            field_name="interfaces",
            dependency=FieldKeyToNameDependency(type_matcher=("net", "interface")),
        )
    ],
    ("net", "route-domain"): [
        SubCollectionDependency(
            field_name="vlans",
            dependency=FieldKeyToNameDependency(
                type_matcher=[("net", "vlan"), ("net", "vlan-group")]
            ),
        ),
    ],
    ("net", "stp"): [
        SubCollectionDependency(
            field_name="vlans",
            dependency=FieldKeyToNameDependency(
                type_matcher=[("net", "vlan"), ("net", "vlan-group")]
            ),
        ),
        SubCollectionDependency(
            field_name="trunks",
            dependency=FieldKeyToNameDependency(type_matcher=("net", "trunk")),
        ),
    ],
    # TODO: Add self-ip object dependencies
}


@dataclass(frozen=True)
class DependencyMap:
    forward: Dict[str, Set[str]]
    reverse: Dict[str, Set[str]]

    def get_dependencies(self, obj_id: str) -> Set[str]:
        """ Build the set of id of objects that given obj uses/depends on"""

        result = set()

        def accumulate(parent: str, child: str):
            result.add(child)

        self.dfs(func=accumulate, _map=self.forward, obj_id=obj_id)

        return result

    def get_dependents(self, obj_id: str) -> Set[str]:
        """ Build the set of id of objects that uses/depends on given obj"""

        result = set()

        def accumulate(parent: str, child: str):
            result.add(child)

        self.dfs(func=accumulate, _map=self.reverse, obj_id=obj_id)

        return result

    @staticmethod
    def dfs(func: Callable[[str, str], Any], _map: Dict[str, Set[str]], obj_id: str):

        visited = set()
        result = set()

        def visit(_id):
            """ Implements a Depth-first search (DFS) algorithm in a graph represented as _map """
            visited.add(_id)
            children = _map[_id] if _id in _map else set()
            result.update(children)
            for child in children:
                if child not in visited:
                    func(parent=_id, child=child)
                    visit(child)

        visit(obj_id)

        return result


def build_dependency_map(config: Config, dependencies_matrix=None) -> DependencyMap:
    """
    Builds a full dependency map (id -> set(id)) for given config object
    """
    if dependencies_matrix is None:
        dependencies_matrix = DEPENDENCIES_MATRIX

    objects = config.fields
    dependency_map = defaultdict(set)
    reverse_dependency_map = defaultdict(set)

    for type_matcher, dependencies in dependencies_matrix.items():
        for obj in objects.get_all(type_matcher):
            for dependency in dependencies:
                result = dependency.find(objects, obj)
                if result:
                    dependency_map[obj.id].update(result)
                    for dependency_id in result:
                        reverse_dependency_map[dependency_id].add(obj.id)

    return DependencyMap(forward=dependency_map, reverse=reverse_dependency_map)
