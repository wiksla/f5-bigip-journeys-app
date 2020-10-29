from itertools import chain
from itertools import product
from typing import Dict
from typing import Iterable
from typing import Set
from typing import Tuple
from typing import Union

import journeys.utils.as3_ops as as3_ops
from journeys.config import Config
from journeys.modifier.conflict.plugins.Plugin import TYPE_NOT_SUPPORTED
from journeys.modifier.conflict.plugins.Plugin import Plugin
from journeys.modifier.conflict.plugins.Plugin import find_as3_object
from journeys.modifier.conflict.plugins.Plugin import find_object_with_type_match
from journeys.modifier.conflict.plugins.Plugin import find_objects_with_field_value
from journeys.modifier.dependency import DependencyMap
from journeys.utils.as3_ops import stringify_declaration


def find_objects_with_string_in_key(
    config: Config,
    type_matcher: Tuple[str, ...],
    string_matcher: Union[str, Iterable[str]],
) -> Set[str]:

    objects = set()

    if isinstance(string_matcher, str):
        string_matcher = [string_matcher]

    for obj_ in config.fields.get_all(type_matcher):
        for field in obj_.fields:
            if any(x in field.key for x in string_matcher):
                objects.add(obj_.id)

    return objects


def find_as3_pem_irules(as3_declaration, irules):
    as3_pem_irules = []
    if not as3_declaration:
        return as3_pem_irules
    for rule in irules:
        if as3_ops.get_json_node(as3_declaration, rule):
            name_list = rule.split("/")
            as3_pem_irules.append((name_list[1], name_list[2], name_list[3]))
    return as3_pem_irules


class Pem(Plugin):
    ID: str = "PEM"
    MSG_INFO: str = "pem"

    IRULES_CMDS = ["CLASSIFICATION::", "CLASSIFY::", "PEM::", "PSC::"]

    MSG_TYPE_1: str = TYPE_NOT_SUPPORTED
    MSG_TYPE_2: str = "Unsupported command in iRule object"
    MSG_TYPE_3: str = "Pem module is not supported"
    AS3_MSG_TYPE_1: str = "This object is incompatible with the destination platform"
    AS3_MSG_TYPE_2: str = "This pointer references an object that is incompatible with the destination platform"

    def __init__(
        self,
        config: Config,
        dependency_map: DependencyMap,
        as3_declaration: Dict,
        as3_file_name: str,
    ):
        self.pem = find_object_with_type_match(config=config, type_matcher=("pem",))
        self.irules = find_objects_with_string_in_key(
            config=config, type_matcher=("ltm", "rule"), string_matcher=self.IRULES_CMDS
        )
        self.provision = find_objects_with_field_value(
            config=config,
            type_matcher=("sys", "provision", "pem"),
            field_name="level",
            field_value=["nominal", "minimum", "dedicated", "custom"],
        )

        # each conf can have a few empty fields which don't mean that pem is enabled
        # ignore the conflict if that is the case
        if not self.provision and not self.irules:
            ignored = {
                "pem global-settings gx",
                "pem global-settings analytics",
                "pem global-settings policy",
            }
            for obj in self.pem:
                if obj not in ignored or len(config.fields[obj].fields) != 0:
                    break
            else:
                self.pem = set()

        self.as3_pem_objects, self.as3_pem_object_pointers = self.find_as3_pem_objects(
            as3_declaration
        )

        self.as3_pem_ltm_irules = find_as3_pem_irules(as3_declaration, self.irules)

        super().__init__(
            config,
            dependency_map,
            self.pem | self.provision | self.irules,
            as3_declaration,
            as3_file_name,
        )

    def delete_objects(self, mutable_config: Config, mutable_as3_declaration: Dict):
        for obj_id in self.pem | self.irules:
            obj = mutable_config.fields.get(obj_id)
            obj.delete()
            if obj_id in self.dependency_map.reverse:
                for related_id in self.dependency_map.reverse[obj_id]:
                    self.dependency_map.apply_resolution(
                        mutable_config, related_id, obj_id
                    )

        for tenant, app, obj in self.as3_pem_objects:
            mutable_as3_declaration[tenant][app].pop(obj)
        for tenant, app, obj, pointer in self.as3_pem_object_pointers:
            mutable_as3_declaration[tenant][app][obj].pop(pointer)
        for tenant, app, obj in self.as3_pem_ltm_irules:
            mutable_as3_declaration[tenant][app].pop(obj)

    def modify_objects(self, mutable_config: Config):
        for obj_id in self.provision:
            obj = mutable_config.fields.get(obj_id)
            field = obj.fields["level"]
            field.value = "none"

    def adjust_objects(self, mutable_config: Config, mutable_as3_declaration: Dict):
        self.delete_objects(
            mutable_config=mutable_config,
            mutable_as3_declaration=mutable_as3_declaration,
        )
        self.modify_objects(mutable_config=mutable_config)

    def mitigations(self):
        return {
            "comment_only": self.comment_objects,
            "recommended": self.adjust_objects,
            "mitigations": {"adjust_objects": self.adjust_objects},
        }

    def generate_object_info(self) -> dict:
        object_info = {}

        for msg, obj_id, field_name in chain(
            product([self.MSG_TYPE_1], self.pem, [self.MSG_INFO]),
            product([self.MSG_TYPE_2], self.irules, [""]),
            product([self.MSG_TYPE_3], self.provision, [""]),
        ):
            obj = self.config.fields.get(obj_id)
            object_info[obj_id] = {
                "file": obj.file,
                "comment": msg.format(field_name),
                "object": str(obj).splitlines(),
            }

        for msg, obj_tuple in chain(
            product([self.AS3_MSG_TYPE_1], self.as3_pem_objects),
            product([self.AS3_MSG_TYPE_2], self.as3_pem_object_pointers),
            product([self.MSG_TYPE_2], self.as3_pem_ltm_irules),
        ):
            obj_id = "/".join(obj_tuple)

            object_info[obj_id] = {
                "file": self.as3_file_name,
                "comment": msg,
                "object": stringify_declaration(
                    find_as3_object(self.as3_declaration, obj_tuple)
                ),
            }

        return object_info

    def find_as3_pem_objects(self, as3_declaration: Dict):
        as3_pem_objects = []
        as3_pem_object_pointers = []

        if not as3_declaration:
            return as3_pem_objects, as3_pem_object_pointers

        data = as3_declaration
        if "declaration" in data:
            data = data["declaration"]

        for tenant, cur_tenant in data.items():
            if not as3_ops.check_matching_type(cur_tenant, {"Tenant"}):
                continue
            for app, cur_app in cur_tenant.items():
                if not as3_ops.check_matching_type(cur_app, {"Application"}):
                    continue
                for obj, cur_obj in cur_app.items():
                    if as3_ops.check_matching_type(cur_obj, self.AS3_PEM_CLASSES):
                        as3_pem_objects.append((tenant, app, obj))
                    elif as3_ops.check_matching_type(cur_obj, self.AS3_VS_CLASSES):
                        for pointer in self.AS3_VS_POINTERS:
                            if pointer in cur_obj:
                                as3_pem_object_pointers.append(
                                    (tenant, app, obj, pointer)
                                )

        return as3_pem_objects, as3_pem_object_pointers

    AS3_PEM_CLASSES = {
        "Bandwidth_Control_Policy",
        "Bandwidth_Control_Policy_Category",
        "Enforcement_Diameter_Endpoint_Profile",
        "Enforcement_Format_Script",
        "Enforcement_Forwarding_Endpoint",
        "Enforcement_Forwarding_Endpoint_Hash_Settings",
        "Enforcement_Interception_Endpoint",
        "Enforcement_iRule",
        "Enforcement_Listener",
        "Enforcement_Policy",
        "Enforcement_Profile",
        "Enforcement_Radius_AAA_Profile",
        "Enforcement_Radius_AAA_Profile_password",
        "Enforcement_Radius_AAA_Profile_sharedSecret",
        "Enforcement_Rule",
        "Enforcement_Rule_Classification_Filter",
        "Enforcement_Rule_DTOS_Tethering",
        "Enforcement_Rule_Flow_Filter",
        "Enforcement_Rule_Forwarding",
        "Enforcement_Rule_Forwarding_Endpoint",
        "Enforcement_Rule_Forwarding_HTTP",
        "Enforcement_Rule_Forwarding_ICAP",
        "Enforcement_Rule_Forwarding_Route_To_Network",
        "Enforcement_Rule_Insert_Content",
        "Enforcement_Rule_Modify_HTTP_Header",
        "Enforcement_Rule_QOS",
        "Enforcement_Rule_Quota",
        "Enforcement_Rule_Ran_Congestion",
        "Enforcement_Rule_Report_Destination_HSL",
        "Enforcement_Rule_URL_Categorization_Filter",
        "Enforcement_Rule_Usage_Gx",
        "Enforcement_Rule_Usage_Hsl",
        "Enforcement_Rule_Usage_Radius",
        "Enforcement_Rule_Usage_Reporting",
        "Enforcement_Rule_Usage_Reporting_Transaction",
        "Enforcement_Rule_Usage_Reporting_Volume",
        "Enforcement_Rule_Usage_Sd",
        "Enforcement_Service_Chain_Endpoint",
        "Enforcement_Service_Chain_Endpoint_Service_Endpoint",
        "Enforcement_Subscriber_Management_Profile",
        "Enforcement_Subscriber_Management_Profile_DHCP",
    }

    AS3_VS_CLASSES = {
        "Service_Forwarding",
        "Service_Generic",
        "Service_HTTP",
        "Service_HTTPS",
        "Service_L4",
        "Service_SCTP",
        "Service_TCP",
        "Service_UDP",
    }

    AS3_VS_POINTERS = (
        "profileDiameterEndpoint",
        "profileEnforcement",
        "profileSubscriberManagement",
        "policyBandwidthControl",
    )
