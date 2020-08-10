from journeys.config import Config
from journeys.modifier.conflict.plugins.Plugin import FIELD_VALUE_NOT_SUPPORTED
from journeys.modifier.conflict.plugins.Plugin import Plugin
from journeys.modifier.conflict.plugins.Plugin import find_objects_with_field_value
from journeys.modifier.dependency import DependencyMap


class MgmtDhcp(Plugin):
    ID: str = "MGMT-DHCP"
    MSG_TYPE: str = FIELD_VALUE_NOT_SUPPORTED
    MSG_INFO: str = "mgmt-dhcp"

    def __init__(self, config: Config, dependency_map: DependencyMap):
        super().__init__(
            config,
            dependency_map,
            find_objects_with_field_value(
                config=config,
                type_matcher=("sys", "global-settings"),
                field_name="mgmt-dhcp",
                field_value=["enabled"],
            ),
        )

    def disable_dhcp(self, mutable_config: Config):
        for obj_id in self.objects:
            obj = mutable_config.fields.get(obj_id)
            field = obj.fields["mgmt-dhcp"]
            field.value = "disabled"
    
    def mitigations(self):
        return {
            "comment_only": self.comment_objects,
            "disable_mgmt_dhcp": self.disable_dhcp
        }