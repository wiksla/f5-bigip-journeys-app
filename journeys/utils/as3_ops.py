import json


def save_declaration(as3_declaration, path: str):
    with open(path, "w") as as3file:
        json.dump(as3_declaration, as3file, indent=2)


def load_declaration(path: str):
    with open(path) as as3file:
        return json.load(as3file)


def stringify_declaration(as3_declaration):
    return json.dumps(as3_declaration, sort_keys=True, indent=2)


def check_matching_type(_obj, class_type):
    return isinstance(_obj, dict) and "class" in _obj and _obj["class"] in class_type


def get_json_node(root, obj_name):
    as3_tree_keys = obj_name.split("/")
    as3_node = root
    for as3_key in as3_tree_keys[1:]:
        if as3_key not in as3_node:
            return None
        as3_node = as3_node[as3_key]
    return as3_node
