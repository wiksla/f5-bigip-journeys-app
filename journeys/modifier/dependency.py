from collections import defaultdict
from dataclasses import dataclass
from functools import partial
from typing import Any
from typing import Callable
from typing import Dict
from typing import List
from typing import Set
from typing import Tuple
from typing import Union

from journeys.config import Config
from journeys.config import Field
from journeys.config import TopLevelField


@dataclass
class BaseDependency:
    parent_types: List[Tuple[str, ...]] = None
    child_types: List[Tuple[str, ...]] = None

    def get_value(self, candidate: Field):
        """Get the value that would connect the candidate with a parent for a given dependency.

        Example:
        net vlan-group test-group {
            vlans {
                test-vlan
            }
        }

        In here test-vlan is the returned value.
        """
        raise NotImplementedError

    def get_target_value(self, candidate: Field):
        """Get the value that would connect the candidate with a child for a given dependency.

        Example:
        net vlan-group test-group {
            vlans {
                test-vlan
            }
        }

        In here test-group should be the returned value.
        """
        raise NotImplementedError

    def match_parent(self, candidate: Field):
        """Test if the candidate matches the 'parent' condition and return the match value.

        By 'parent' we understand a field on which other fields can depend.
        """
        for type_ in self.parent_types:
            if tuple(candidate.args[: len(type_)]) == type_:
                yield from self.get_target_value(candidate)

    def match_child(self, candidate: Field):
        """Test if the candidate matches the 'child' condition and return the match value.

        By 'child' we understand a field which depends on existence of another field.
        """
        for type_ in self.child_types:
            if tuple(candidate.args[: len(type_)]) == type_:
                yield from self.get_value(candidate)

    def get_resolve(
        self, obj: Field, value: str
    ) -> Callable[[Union[Config, Field]], None]:
        """Get a method that should modify the given Parent (Config or Field) so that the dependency
        to a field using the given value disappears.

        By defaults deletes the whole Field.
        @param obj: the Field in which the dependency is found.
        @param value: a value connecting the two sides of a dependency."""

        def delete(parent):
            parent.fields[obj.key].delete()

        return delete


@dataclass
class FromFieldValueDependencyMixIn:
    field_name: str = None
    resolution: str = "delete_child"  # oneof: delete_child, delete_self

    def get_value(self, obj) -> str:
        try:
            field = obj.fields[self.field_name]
            yield field.value
        except KeyError:
            pass

    def get_resolve(
        self, obj: Field, value: str
    ) -> Callable[[Union[Config, Field]], None]:
        def delete_self(parent):
            try:
                parent.fields[obj.key].delete()
            except KeyError:
                pass  # given object was already deleted

        def delete_child(parent):
            try:
                parent.fields[obj.key].fields[self.field_name].delete()
            except KeyError:
                pass  # given child was already deleted

        if self.resolution == "delete_child":
            return delete_child
        else:
            return delete_self


@dataclass
class FromFieldKeyDependencyMixIn:
    def get_value(self, obj) -> str:
        yield obj.key


@dataclass
class FromNameDependencyMixIn:
    def get_value(self, obj) -> str:
        yield obj.name


@dataclass
class ToNameDependencyMixIn:
    def get_target_value(self, obj: Field) -> str:
        # a bit messy, probably should split up the 'From' and 'To' parts
        # into different objects
        while not isinstance(obj, TopLevelField):
            obj = obj.parent
        yield obj.name


@dataclass
class ToFieldValueDependencyMixIn:
    target_field_name: str = None

    def get_target_value(self, obj) -> str:
        try:
            yield obj.fields[self.target_field_name].value
        except KeyError:
            pass


@dataclass
class FieldValueToNameDependency(
    FromFieldValueDependencyMixIn, ToNameDependencyMixIn, BaseDependency
):
    pass


@dataclass
class FieldValueToFieldValueDependency(
    FromFieldValueDependencyMixIn, ToFieldValueDependencyMixIn, BaseDependency
):
    pass


@dataclass
class FieldKeyToNameDependency(
    FromFieldKeyDependencyMixIn, ToNameDependencyMixIn, BaseDependency
):
    pass


@dataclass
class NameToNameDependency(
    FromNameDependencyMixIn, ToNameDependencyMixIn, BaseDependency
):
    pass


@dataclass
class SubCollectionDependency(BaseDependency):
    """ Dependency class that allows to find dependencies of each item in a subcollection named field_name

    Attributes:
        field_name (str): name of the field that contains a subcollection of items
        dependency (BaseDependency): dependency object to check the subcollection items against
    """

    field_name: str = None
    dependency: BaseDependency = None
    resolution: str = "nested"  # oneof: nested, delete

    def get_resolve(
        self, obj: Field, value: str
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

        for sub_obj in obj.fields[self.field_name].fields:
            if value in self.dependency.get_value(sub_obj):
                collection_resolves.append(self.dependency.get_resolve(sub_obj, value))

        if self.resolution == "nested":
            return nested_all
        elif self.resolution == "nested_with_cleanup":
            return nested_with_cleanup
        else:
            return delete

    def get_value(self, candidate: Field):
        try:
            members = candidate.fields[self.field_name].fields
        except KeyError:
            members = []

        for sub_obj in members:
            yield from self.dependency.get_value(sub_obj)

    def get_target_value(self, candidate: Field):
        yield from self.dependency.get_target_value(candidate)


@dataclass
class NestedDependency(BaseDependency):
    """Looks for dependencies in an object under a given key.

    Contrary to SubcollectionDependency, it doesn't implicitly
    iterate over members of the given key."""

    field_name: str = None
    dependency: BaseDependency = None
    resolution: str = "nested"  # oneof: nested, delete

    def get_resolve(
        self, obj: Field, value: str
    ) -> Callable[[Union[Config, Field]], None]:
        def delete(parent):
            parent.fields[obj.key].fields[self.field_name].delete()

        def nested(parent, resolution):
            resolution(parent.fields[obj.key])

        if self.resolution == "nested":
            nested_resolution = self.dependency.get_resolve(
                obj.fields[self.field_name], value
            )
            return partial(nested, resolution=nested_resolution)
        else:
            return delete

    def get_value(self, candidate: Field):
        try:
            sub_obj = candidate.fields[self.field_name]
        except KeyError:
            pass
        else:
            yield from self.dependency.get_value(sub_obj)

    def get_target_value(self, candidate: Field):
        yield from self.dependency.get_target_value(candidate)


DEFAULT_DEPENDENCIES = [
    SubCollectionDependency(
        child_types=[("gtm", "listener")],
        field_name="vlans",
        parent_types=[("net", "vlan"), ("net", "vlan-group")],
        dependency=FieldKeyToNameDependency(),
    ),
    FieldValueToNameDependency(
        child_types=[("ltm", "pool")],
        field_name="monitor",
        parent_types=[("ltm", "monitor")],
    ),
    SubCollectionDependency(
        child_types=[("ltm", "pool")],
        field_name="members",
        parent_types=[("ltm", "monitor")],
        dependency=FieldValueToNameDependency(field_name="monitor"),
    ),
    SubCollectionDependency(
        child_types=[("ltm", "pool")],
        field_name="members",
        parent_types=[("ltm", "node")],
        dependency=FieldValueToFieldValueDependency(
            field_name="address", target_field_name="address"
        ),
    ),
    SubCollectionDependency(
        child_types=[
            ("ltm", "nat"),
            ("ltm", "snat"),
            ("ltm", "virtual"),
            ("net", "packet-filter-trusted"),
            ("net", "route-domain"),
            ("net", "stp"),
        ],
        field_name="vlans",
        parent_types=[("net", "vlan"), ("net", "vlan-group")],
        dependency=FieldKeyToNameDependency(),
    ),
    NameToNameDependency(
        child_types=[("net", "fdb", "vlan")], parent_types=[("net", "vlan")]
    ),
    SubCollectionDependency(
        child_types=[("net", "fdb", "vlan")],
        field_name="records",
        parent_types=[("net", "trunk")],
        dependency=FieldValueToNameDependency(field_name="trunk"),
    ),
    SubCollectionDependency(
        child_types=[("net", "fdb", "vlan")],
        field_name="records",
        parent_types=[("net", "interface")],
        dependency=FieldValueToNameDependency(field_name="interface"),
    ),
    FieldValueToNameDependency(
        child_types=[("net", "packet-filter")],
        field_name="vlan",
        parent_types=[("net", "vlan"), ("net", "vlan-group")],
    ),
    FieldValueToNameDependency(
        child_types=[("net", "self")],
        field_name="vlan",
        parent_types=[("net", "vlan"), ("net", "vlan-group")],
        resolution="delete_self",
    ),
    FieldValueToNameDependency(
        child_types=[("net", "route")],
        field_name="interface",
        parent_types=[("net", "vlan"), ("net", "vlan-group")],
    ),
    SubCollectionDependency(
        child_types=[("net", "stp"), ("sys", "ha-group")],
        field_name="trunks",
        parent_types=[("net", "trunk")],
        dependency=FieldKeyToNameDependency(),
        resolution="nested_with_cleanup",
    ),
    SubCollectionDependency(
        child_types=[("net", "trunk")],
        field_name="interfaces",
        parent_types=[("net", "interface")],
        dependency=FieldKeyToNameDependency(),
        resolution="nested_with_cleanup",
    ),
    SubCollectionDependency(
        child_types=[("net", "vlan")],
        field_name="interfaces",
        parent_types=[("net", "trunk")],
        dependency=FieldKeyToNameDependency(),
        resolution="nested_with_cleanup",
    ),
    SubCollectionDependency(
        child_types=[("net", "vlan-group")],
        field_name="members",
        parent_types=[("net", "vlan")],
        dependency=FieldKeyToNameDependency(),
    ),
    SubCollectionDependency(
        child_types=[
            ("security", "firewall", "management-ip-rules"),
            ("security", "firewall", "policy"),
            ("security", "firewall", "rule-list"),
            ("security", "nat", "policy"),
        ],
        field_name="rules",
        parent_types=[("net", "vlan"), ("net", "vlan-group")],
        dependency=NestedDependency(
            field_name="source",
            dependency=SubCollectionDependency(
                field_name="vlans", dependency=FieldKeyToNameDependency(),
            ),
        ),
    ),
    SubCollectionDependency(
        child_types=[("security", "nat", "policy")],
        field_name="rules",
        parent_types=[("net", "vlan"), ("net", "vlan-group")],
        dependency=NestedDependency(
            field_name="next-hop",
            dependency=FieldValueToNameDependency(field_name="vlan",),
        ),
    ),
    FieldValueToNameDependency(
        child_types=[("security", "dos", "network-whitelist")],
        field_name="address-list",
        parent_types=[
            ("net", "address-list"),
            ("security", "firewall", "address-list"),
            ("security", "shared-objects", "address-list"),
        ],
        resolution="delete_self",
    ),
]


class DependencyMap:
    def __init__(self, config, dependencies=DEFAULT_DEPENDENCIES):
        children = defaultdict(
            lambda: defaultdict(set)
        )  # {dependency: {match_value: {field_id}}}
        parents = defaultdict(lambda: defaultdict(set))
        resolutions = dict()
        dependency_id_map = dict()
        for field in config.fields.all():
            for dependency in dependencies:
                dependency_id_map[id(dependency)] = dependency
                for value in dependency.match_child(field):
                    children[id(dependency)][value].add(field.id)
                for value in dependency.match_parent(field):
                    parents[id(dependency)][value].add(field.id)

        map_ = defaultdict(set)

        for dependency_id, match in children.items():
            for value, child_ids in match.items():
                if value in parents[dependency_id]:
                    for parent_id in parents[dependency_id][value]:
                        map_[parent_id] |= child_ids
                        for child_id in child_ids:
                            dependency = dependency_id_map[dependency_id]
                            resolutions[(child_id, parent_id)] = dependency.get_resolve(
                                config.fields[child_id], value
                            )

        self.resolutions = resolutions
        self.reverse = dict(map_)
        self.forward = self._reverse_graph(self.reverse)

    def _reverse_graph(self, graph):
        reverse = defaultdict(set)
        for edge_start, ends in graph.items():
            for edge_end in ends:
                reverse[edge_end].add(edge_start)
        return dict(reverse)

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
