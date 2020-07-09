from collections import defaultdict
from dataclasses import dataclass
from typing import Tuple

from journeys.config import Config
from journeys.config import Field
from journeys.config import FieldCollection


@dataclass
class FieldDependency:
    """Base class for all Field value related dependencies.

    Attributes:
        field_name (str): Name of the field which would be used from object that is being checked.
        type_matcher (Tuple[str, ...]): Pattern to use for searching dependency candidates.
    """

    field_name: str
    type_matcher: Tuple[str, ...]

    def find(self, objects: FieldCollection, obj: Field):
        """Finds obj dependency among objects.

        Dependency search is done by:
        - retrieving a value from field named by field_name
        - finding dependency candidates with use of type_matcher
        - finding a dependency among the candidates by comparing a value retrieved from candidate object
        with value retrieved from obj field named field_name.
        """
        try:
            field = obj.fields[self.field_name]
            value = field.value
        except KeyError:
            return []

        ret = []
        for candidate in objects.get_all(self.type_matcher):

            if self.get_target_value(candidate) == value:
                ret.append(candidate.id)

        return ret

    def get_target_value(self, obj):
        """ Gets a value from a dependency candidate to compare it with value of the field named by field_name."""
        raise NotImplementedError()


@dataclass
class FieldToNameDependency(FieldDependency):
    """ Subclass of FieldDependency that takes a dependency candidate name as a value"""

    def get_target_value(self, obj: Field):
        return obj.name


@dataclass
class FieldToFieldDependency(FieldDependency):
    """ Subclass of FieldDependency that takes a dependency candidate field named target_field_name as a value"""

    target_field_name: str

    def get_target_value(self, obj):
        return obj.fields[self.target_field_name].value


@dataclass
class SubCollectionDependency:
    """ Dependency class that allows to find dependencies of each item in a subcollection named field_name

    Attributes:
        field_name (str): name of the field that contains a subcollection of items
        dependency (FieldDependency): dependency object to check the subcollection items against
    """

    field_name: str
    dependency: FieldDependency

    def find(self, objects: FieldCollection, obj: Field):
        members = obj.fields[self.field_name].fields
        ret = []

        for sub_obj in members:
            sub_ret = self.dependency.find(objects, sub_obj)
            if sub_ret:
                ret.extend(sub_ret)

        return ret


monitor_dependency = FieldToNameDependency(
    field_name="monitor", type_matcher=("ltm", "monitor")
)

DEPENDENCIES_MATRIX = {
    ("ltm", "pool"): [
        monitor_dependency,
        SubCollectionDependency(field_name="members", dependency=monitor_dependency),
        SubCollectionDependency(
            field_name="members",
            dependency=FieldToFieldDependency(
                field_name="address",
                type_matcher=("ltm", "node"),
                target_field_name="address",
            ),
        ),
    ]
}


def build_dependency_map(config: Config, dependencies_matrix=None):
    """
    Builds a full dependency map (id -> set(id)) for given config object
    """
    if dependencies_matrix is None:
        dependencies_matrix = DEPENDENCIES_MATRIX

    objects = config.fields
    result = defaultdict(set)

    for type_matcher, dependencies in dependencies_matrix.items():
        for obj in objects.get_all(type_matcher):
            for dependency in dependencies:
                sub_result = dependency.find(objects, obj)
                if sub_result:
                    result[obj.id].update(sub_result)

    return result
