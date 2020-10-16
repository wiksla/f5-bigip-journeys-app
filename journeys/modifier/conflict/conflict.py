from dataclasses import dataclass
from dataclasses import field as dataclass_field
from typing import Callable
from typing import Dict
from typing import List
from typing import Set


@dataclass
class Conflict:
    """This is a class that represents a conflict

    Attributes:
        id (str): Code name for a conflict

        summary (List[str]): Brief description of a conflict
        affected_objects (List[Dict[str,str]]): Objects that causes conflicts with descriptions
        files_to_render (Set[str]): files to be rendered for each mitigation
        mitigations (Dict[str, Callable[Config]]): name -> mitigation method mapping
    """

    id: str
    summary: List[str]
    affected_objects: Dict[str, Dict]
    files_to_render: Set[str] = dataclass_field(default_factory=set)
    mitigations: Dict[str, Callable] = dataclass_field(default_factory=dict)
