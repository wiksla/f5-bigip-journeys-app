import os
from functools import partial

from journeys.config import Config
from journeys.modifier.conflict.plugins.Plugin import find_object_with_type_match
from journeys.utils.image import Version
from journeys.utils.image import parse_version_file


class UcsReader:
    """ Component used to get data from extracted ucs """

    def __init__(self, extracted_ucs_dir):
        self.ucs_path = partial(os.path.join, extracted_ucs_dir)

    def get_platform(self) -> str:
        """ keys: platform, family, host, systype """
        ucs_platform_fn = self.ucs_path("config/.ucs_platform")

        def _parse_ucs_platform(ucs_platform):
            return dict(
                (line.split("=")[0].lower(), line.split("=")[1].strip())
                for line in ucs_platform
            )

        with open(ucs_platform_fn) as ucs_platform_fd:
            return _parse_ucs_platform(ucs_platform=ucs_platform_fd)["platform"]

    def get_config(self) -> Config:
        return Config.from_dir(self.ucs_path("config"))

    def get_version(self) -> Version:
        ucs_version_fn = self.ucs_path("config/ucs_version")

        with open(ucs_version_fn) as version_fd:
            return Version(**parse_version_file(version_fd.read()))

    def get_provisioned_modules(self) -> dict:
        bigip_base_conf = Config.from_conf(
            filename=self.ucs_path("config/bigip_base.conf")
        )
        provisioned_module_obj = find_object_with_type_match(
            config=bigip_base_conf, type_matcher=("sys", "provision")
        )

        def _get_modules_level(provisioned_module_obj):
            provisioning_mapping = {}
            for module_ in provisioned_module_obj:
                obj = bigip_base_conf.fields.get(module_)
                provisioning_mapping[obj.name] = obj.fields[0].value
            return provisioning_mapping

        return _get_modules_level(provisioned_module_obj)
