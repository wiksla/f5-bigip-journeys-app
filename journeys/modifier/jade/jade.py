import os

from journeys.config import Config
from journeys.modifier.conflict.plugins.Plugin import find_object_with_type_match
from journeys.modifier.dependency import DependencyMap


class JadeEngine:
    def __init__(self, config: Config, applications_root_dir: str):
        self.config = config
        self.applications_root_dir = applications_root_dir
        self.dependency_map = DependencyMap(self.config)

    def explode(self):

        virtual_servers = find_object_with_type_match(
            config=self.config, type_matcher=("ltm", "virtual")
        )

        for virtual_server in virtual_servers:
            objects = self.dependency_map.get_dependencies(virtual_server)
            objects.add(virtual_server)

            application_config = Config.from_string("")

            for obj_id in objects:
                obj = self.config.fields.get(obj_id)
                application_config.field_collection.add_data(obj.data, copy=False)

            application_name = self.config.fields.get(virtual_server).name.replace(
                os.path.sep, "_"
            )
            dirname = os.path.join(self.applications_root_dir, application_name)
            os.mkdir(dirname)

            application_config.build(dirname=dirname)
