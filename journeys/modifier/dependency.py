from collections import defaultdict
from dataclasses import dataclass
from dataclasses import field
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


class BaseDependency:
    def find(self, objects: FieldCollection, obj: Field) -> List[str]:
        """A method that should return a list of ids of dependent objects."""
        raise NotImplementedError

    def get_resolve(
        self, obj: Field, target_id: str
    ) -> Callable[[Union[Config, Field]], None]:
        """Get a method that should modify the given Parent (Config or Field) so that the dependency
        to a field having the id target_id disappears.

        By defaults deletes the whole Field.
        @param obj: the Field in which the dependency is found.
        @param target_id: id of the top level Field connected by the dependency."""

        def delete(parent):
            parent.fields[obj.key].delete()

        return delete


@dataclass
class FieldDependencyMixIn(BaseDependency):
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
                try:
                    if self.get_target_value(obj=candidate) == value:
                        ret.append(candidate.id)
                except KeyError:
                    pass

        return ret


@dataclass
class FromFieldValueDependencyMixIn:
    field_name: str
    resolution: str = "delete_child"  # oneof: delete_child, delete_self

    def get_value(self, obj) -> str:
        field = obj.fields[self.field_name]
        return field.value

    def get_resolve(
        self, obj: Field, target_id: str
    ) -> Callable[[Union[Config, Field]], None]:
        def delete_self(parent):
            parent.fields[obj.key].delete()

        def delete_child(parent):
            parent.fields[obj.key].fields[self.field_name].delete()

        if self.resolution == "delete_child":
            return delete_child
        else:
            return delete_self


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
class SubCollectionDependency(BaseDependency):
    """ Dependency class that allows to find dependencies of each item in a subcollection named field_name

    Attributes:
        field_name (str): name of the field that contains a subcollection of items
        dependency (FieldDependencyMixIn): dependency object to check the subcollection items against
    """

    field_name: str
    dependency: BaseDependency
    resolution: str = "nested"  # oneof: nested, delete
    found: dict = field(
        default_factory=lambda: defaultdict(list)
    )  # {(from, to): [connecting_block1,..]}

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
                for item in sub_ret:
                    self.found[(obj.key, item)].append(sub_obj)

        return ret

    def get_resolve(
        self, obj: Field, target_id: str
    ) -> Callable[[Union[Config, Field]], None]:
        collection_resolves = []

        def delete(parent):
            parent.fields[obj.key].fields[self.field_name].delete()

        def nested_all(parent):
            # handle a case where there might be multiple dependencies to the same
            # target object in a single collection - iterate over them all
            collection_field = parent.fields[obj.key].fields[self.field_name]
            for resolve in collection_resolves:
                resolve(collection_field)

        def nested_with_cleanup(parent):
            nested_all(parent)
            collection_field = parent.fields[obj.key].fields[self.field_name]
            if not list(collection_field.fields.all()):
                delete(parent)

        for sub_obj in self.found[(obj.key, target_id)]:
            collection_resolves.append(self.dependency.get_resolve(sub_obj, target_id))

        if self.resolution == "nested":
            return nested_all
        elif self.resolution == "nested_with_cleanup":
            return nested_with_cleanup
        else:
            return delete


@dataclass
class NestedDependency(BaseDependency):
    """Looks for dependencies in an object under a given key.

    Contrary to SubcollectionDependency, it doesn't implicitly
    iterate over members of the given key."""

    field_name: str
    dependency: BaseDependency
    resolution: str = "nested"  # oneof: nested, delete

    def find(self, objects: FieldCollection, obj: Field) -> List[str]:
        ret = []

        try:
            sub_obj = obj.fields[self.field_name]
        except KeyError:
            return ret

        sub_ret = self.dependency.find(objects, sub_obj)
        if sub_ret:
            ret.extend(sub_ret)

        return ret

    def get_resolve(
        self, obj: Field, target_id: str
    ) -> Callable[[Union[Config, Field]], None]:
        def delete(parent):
            parent.fields[obj.key].fields[self.field_name].delete()

        if self.resolution == "nested":
            return self.dependency.get_resolve(obj.fields[self.field_name], target_id)
        else:
            return delete


monitor_dependency = FieldValueToNameDependency(
    field_name="monitor", type_matcher=("ltm", "monitor")
)
sec_rules_source_vlan = SubCollectionDependency(
    field_name="rules",
    dependency=NestedDependency(
        field_name="source",
        dependency=SubCollectionDependency(
            field_name="vlans",
            dependency=FieldKeyToNameDependency(
                type_matcher=[("net", "vlan"), ("net", "vlan-group")]
            ),
        ),
    ),
)

DEPENDENCIES_MATRIX = {
    ("gtm", "listener"): [
        SubCollectionDependency(
            field_name="vlans",
            dependency=FieldKeyToNameDependency(
                type_matcher=[("net", "vlan"), ("net", "vlan-group")]
            ),
        )
    ],
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
    ("ltm", "nat"): [
        SubCollectionDependency(
            field_name="vlans",
            dependency=FieldKeyToNameDependency(
                type_matcher=[("net", "vlan"), ("net", "vlan-group")]
            ),
        )
    ],
    ("ltm", "snat"): [
        SubCollectionDependency(
            field_name="vlans",
            dependency=FieldKeyToNameDependency(
                type_matcher=[("net", "vlan"), ("net", "vlan-group")]
            ),
        )
    ],
    ("ltm", "virtual"): [
        SubCollectionDependency(
            field_name="vlans",
            dependency=FieldKeyToNameDependency(
                type_matcher=[("net", "vlan"), ("net", "vlan-group")]
            ),
        )
    ],
    ("net", "fdb", "vlan"): [
        NameToNameDependency(type_matcher=("net", "vlan")),
        SubCollectionDependency(
            field_name="records",
            dependency=FieldValueToNameDependency(
                field_name="trunk", type_matcher=("net", "trunk")
            ),
        ),
        SubCollectionDependency(
            field_name="records",
            dependency=FieldValueToNameDependency(
                field_name="interface", type_matcher=("net", "interface")
            ),
        ),
    ],
    ("net", "packet-filter"): [
        FieldValueToNameDependency(
            field_name="vlan", type_matcher=[("net", "vlan"), ("net", "vlan-group")]
        )
    ],
    ("net", "packet-filter-trusted"): [
        SubCollectionDependency(
            field_name="vlans",
            dependency=FieldKeyToNameDependency(
                type_matcher=[("net", "vlan"), ("net", "vlan-group")]
            ),
        ),
    ],
    ("net", "route"): [
        FieldValueToNameDependency(
            field_name="interface",
            type_matcher=[("net", "vlan"), ("net", "vlan-group")],
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
    ("net", "self"): [
        FieldValueToNameDependency(
            field_name="vlan",
            type_matcher=[("net", "vlan"), ("net", "vlan-group")],
            resolution="delete_self",  # vlan property is required for self-ip, cannot remove only it
        )
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
            resolution="nested_with_cleanup",
        ),
    ],
    ("net", "trunk"): [
        SubCollectionDependency(
            field_name="interfaces",
            dependency=FieldKeyToNameDependency(type_matcher=("net", "interface")),
            resolution="nested_with_cleanup",
        )
    ],
    ("net", "vlan"): [
        SubCollectionDependency(
            field_name="interfaces",
            dependency=FieldKeyToNameDependency(type_matcher=("net", "trunk")),
            resolution="nested_with_cleanup",
        ),
    ],
    ("net", "vlan-group"): [
        SubCollectionDependency(
            field_name="members",
            dependency=FieldKeyToNameDependency(type_matcher=("net", "vlan")),
        )
    ],
    ("security", "firewall", "management-ip-rules"): [sec_rules_source_vlan],
    ("security", "firewall", "policy"): [sec_rules_source_vlan],
    ("security", "firewall", "rule-list"): [sec_rules_source_vlan],
    ("security", "nat", "policy"): [
        sec_rules_source_vlan,
        SubCollectionDependency(
            field_name="rules",
            dependency=NestedDependency(
                field_name="next-hop",
                dependency=FieldValueToNameDependency(
                    field_name="vlan",
                    type_matcher=[("net", "vlan"), ("net", "vlan-group")],
                ),
            ),
        ),
    ],
    ("sys", "ha-group"): [
        SubCollectionDependency(
            field_name="trunks",
            dependency=FieldKeyToNameDependency(type_matcher=("net", "trunk")),
            resolution="nested_with_cleanup",
        ),
    ]
    # TODO: Add self-ip object dependencies
}


@dataclass(frozen=True)
class DependencyMap:
    forward: Dict[str, Set[str]]
    reverse: Dict[str, Set[str]]
    resolutions: Dict[Tuple[str, str], Callable]

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
    resolutions = dict()

    for type_matcher, dependencies in dependencies_matrix.items():
        for obj in objects.get_all(type_matcher):
            for dependency in dependencies:
                result = dependency.find(objects, obj)
                if result:
                    dependency_map[obj.id].update(result)
                    for dependency_id in result:
                        resolutions[(obj.id, dependency_id)] = dependency.get_resolve(
                            obj, dependency_id
                        )
                        reverse_dependency_map[dependency_id].add(obj.id)

    return DependencyMap(
        forward=dependency_map, reverse=reverse_dependency_map, resolutions=resolutions
    )
