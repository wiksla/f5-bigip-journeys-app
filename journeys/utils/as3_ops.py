import json


def save_declaration(as3_declaration, path: str):
    with open(path, "w") as as3file:
        json.dump(as3_declaration, as3file, indent=2)


def load_declaration(path: str):
    with open(path) as as3file:
        return json.load(as3file)


def stringify_declaration(as3_declaration):
    return json.dumps(as3_declaration, sort_keys=True, indent=2)
