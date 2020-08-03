import importlib
import inspect
from pathlib import Path
from pkgutil import iter_modules
from typing import List
from typing import Type

from journeys.modifier.conflict.plugins.Plugin import Plugin


def load_plugins() -> List[Type[Plugin]]:
    plugins = []
    package_dir = Path(__file__).resolve().parent
    for (_, module_name, _) in iter_modules([package_dir]):
        for member in inspect.getmembers(
            importlib.import_module("." + module_name, __name__), inspect.isclass
        ):
            cls = member[1]
            if issubclass(cls, Plugin) and cls is not Plugin:
                plugins.append(cls)
    return plugins
