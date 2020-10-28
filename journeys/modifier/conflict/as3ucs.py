import base64
import re

import journeys.utils.as3_ops as as3_ops
from journeys.config import Config
from journeys.config import Field
from journeys.config import FieldCollection


class As3ucs:
    def __init__(self, declaration):
        self.data = declaration
        self.partitions = []
        self.pointer = self.data
        if "declaration" in self.pointer:
            self.pointer = self.pointer["declaration"]

        for item in self.pointer:
            if isinstance(self.pointer[item], dict):
                if item == "Common":
                    self.partitions.append("Common/Shared")
                    continue
                self.partitions.append(item)

    def process_ucs_changes(self, config: Config):
        if len(self.partitions) == 0:
            return

        pattern_str = "^("
        first = True
        for chunk in self.partitions:
            if first:
                first = False
            else:
                pattern_str += "|"
            pattern_str = pattern_str + "/" + chunk
        pattern_str += ")"
        pattern = re.compile(pattern_str)

        conflict_list = [
            (
                config.fields.get_all(("security", "nat", "source-translation")),
                ["egress-interfaces"],
                As3ucs._handle_net_source_translation,
            ),
            (
                config.fields.get_all(("ltm", "virtual")),
                ["vlans"],
                As3ucs._handle_ltm_vlans,
            ),
            (
                config.fields.get_all(("security", "firewall", "rule-list")),
                ["rules"],
                As3ucs._handle_security_rulelist,
            ),
            (
                config.fields.get_all(("security", "firewall", "policy")),
                ["rules"],
                As3ucs._handle_security_policy,
            ),
        ]

        for conflict in conflict_list:
            objects = conflict[0]
            for field in objects:
                name = field.name
                fields = field.fields
                if pattern.match(name) is not None:
                    as3_node = as3_ops.get_json_node(self.pointer, name)
                    if as3_node is not None:
                        source_field = As3ucs._find_subfield(fields, conflict[1])
                        if source_field is not None:
                            conflict[2](as3_node, source_field)

    def decode_as3_irules(self):
        decoded_irules = []
        for tenant, cur_tenant in self.pointer.items():
            if not as3_ops.check_matching_type(cur_tenant, {"Tenant"}):
                continue
            for app, cur_app in cur_tenant.items():
                if not as3_ops.check_matching_type(cur_app, {"Application"}):
                    continue
                for obj, cur_obj in cur_app.items():
                    if (
                        as3_ops.check_matching_type(cur_obj, {"iRule"})
                        and isinstance(cur_obj["iRule"], dict)
                        and "base64" in cur_obj["iRule"]
                    ):
                        decoded_irules.append((tenant, app, obj))
                        cur_obj["iRule"] = base64.b64decode(
                            cur_obj["iRule"]["base64"]
                        ).decode("utf8")

        return decoded_irules

    def encode_as3_irules(self, rule_list):
        for tenant, app, obj in rule_list:
            try:
                node = self.pointer[tenant][app][obj]
                body = node["iRule"]
                encoded = base64.b64encode(body.encode("utf8")).decode("utf8")
                node["iRule"] = {"base64": encoded}
            except KeyError:
                pass  # iRule was removed

    @staticmethod
    def _find_subfield(fields: FieldCollection, field_tuple) -> Field:
        field: Field = None
        for field_key in field_tuple:
            try:
                field = fields.get(field_key)
                fields = field.fields
            except KeyError:
                return None
        return field

    @staticmethod
    def _handle_ltm_vlans(as3_node, source_field):
        As3ucs._process_vlan_array(as3_node, "allowVlans", "rejectVlans", source_field)

    @staticmethod
    def _handle_net_source_translation(as3_node, source_field):
        As3ucs._process_vlan_array(
            as3_node, "allowEgressInterfaces", "disallowEgressInterfaces", source_field
        )

    @staticmethod
    def _process_vlan_array(as3_node, key_option1, key_option2, source_field):
        as3_key = key_option1
        if as3_key not in as3_node:
            as3_key = key_option2
            if as3_key not in as3_node:
                return  # No vlans originally, nothing to do
        as3_node[as3_key] = As3ucs._render_vlan_array(source_field)

    @staticmethod
    def _handle_security_rulelist(as3_node, source_field):
        if "rules" not in as3_node:  # policy with no rules
            return
        as3_node = as3_node["rules"]
        field_num = len(source_field.fields)
        if len(as3_node) != field_num:
            return
        for it in range(field_num):
            As3ucs._handle_security_rule(as3_node[it], source_field.fields.get(it))

    @staticmethod
    def _handle_security_rule(as3_node, ucs_data):
        if "source" not in as3_node:
            return
        if "vlans" not in as3_node["source"]:
            return
        try:
            source_list = ucs_data.fields.get("source")
        except KeyError:
            as3_node.pop("source", None)
            return
        try:
            vlan_list = source_list.fields.get("vlans")
        except KeyError:
            as3_node["source"].pop("vlans", None)
            return
        as3_node["source"]["vlans"] = As3ucs._render_vlan_array(vlan_list)

    @staticmethod
    def _handle_security_policy(as3_node, source_field):
        if "rules" not in as3_node:  # policy with no rules
            return
        as3_node = as3_node["rules"]
        rule_num = len(source_field.fields)
        for it in range(rule_num):
            if "use" in as3_node[it] or "bigip" in as3_node[it]:
                continue  # it is a rule-list reference, will be handled as a separate object
            As3ucs._handle_security_rule(as3_node[it], source_field.fields.get(it))

    @staticmethod
    def _render_vlan_array(source_field):
        ret_val = [{"bigip": vlan.key} for vlan in source_field.fields.all()]
        return ret_val
