import json
import re

from journeys.config import Config
from journeys.config import Field
from journeys.config import FieldCollection


class As3ucs:
    def __init__(self, input_as3: str):
        with open(input_as3) as as3file:
            self.data = json.load(as3file)
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
                    as3_node = self._get_as3_node(name)
                    if as3_node is not None:
                        source_field = As3ucs._find_subfield(fields, conflict[1])
                        if source_field is not None:
                            conflict[2](as3_node, source_field)

    def save_declaration(self, path: str):
        with open(path, "w") as as3file:
            json.dump(self.data, as3file, indent=2)

    def get_declaration_string(self):
        return json.dumps(self.data, sort_keys=True, indent=2)

    def _get_as3_node(self, obj_name):
        as3_tree_keys = obj_name.split("/")
        as3_node = self.pointer
        for as3_key in as3_tree_keys[1:]:
            if as3_key not in as3_node:
                return None
            as3_node = as3_node[as3_key]
        return as3_node

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
        as3_key = "allowVlans"
        if as3_key not in as3_node:
            as3_key = "rejectVlans"
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
