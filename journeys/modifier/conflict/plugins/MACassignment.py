import configparser

from journeys.config import Config
from journeys.modifier.conflict.plugins.Plugin import FIELD_VALUE_NOT_SUPPORTED
from journeys.modifier.conflict.plugins.Plugin import Plugin
from journeys.modifier.conflict.plugins.Plugin import find_objects_with_field_value
from journeys.modifier.dependency import DependencyMap


# TODO: It's not FODE it should be part of future module (fixup-script diagnostics or smth)
class VLANMACassignment(Plugin):
    ID: str = "VLANMACassignment"
    MSG_TYPE: str = FIELD_VALUE_NOT_SUPPORTED
    MSG_INFO: str = "share-single-mac"

    def __init__(self, config: Config, dependency_map: DependencyMap):

        super().__init__(
            config,
            dependency_map,
            find_objects_with_field_value(
                config=config,
                type_matcher=("ltm", "global-settings", "general"),
                field_name="share-single-mac",
                field_value=["vmw-compat"],
            ),
        )

    @staticmethod
    def check_vlan_mac_assignment_value(config):
        try:
            return (
                config.bigdb.get(section="Vlan.MacAssignment", option="value")
                == "vmw-compat"
            )
        except configparser.NoOptionError:
            return False

    def set_vlan_mac_assignment_to_unique(self, mutable_config: Config):
        share_single_mac = self._find_value_field(mutable_config=mutable_config)
        share_single_mac.value = "unique"
        mutable_config.bigdb.set(
            section="Vlan.MacAssignment", option="value", value="unique"
        )

    def set_vlan_mac_assignment_to_global(self, mutable_config: Config):
        share_single_mac = self._find_value_field(mutable_config=mutable_config)
        share_single_mac.value = "global"
        mutable_config.bigdb.set(
            section="Vlan.MacAssignment", option="value", value="global"
        )

    def _find_value_field(self, mutable_config: Config):
        for obj_id in self.objects:
            obj = mutable_config.fields.get(obj_id)
            return obj.fields["share-single-mac"]

    def mitigations(self) -> dict:
        return {
            "comment_only": self.comment_objects,
            "recommended": self.set_vlan_mac_assignment_to_unique,
            "mitigations": {
                "share_single_mac_global": self.set_vlan_mac_assignment_to_global,
                "share_single_mac_unique": self.set_vlan_mac_assignment_to_unique,
            },
        }
