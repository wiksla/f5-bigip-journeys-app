from difflib import unified_diff
from typing import Dict

from deepdiff import DeepDiff
from deepdiff.helper import get_type

from journeys.errors import InputError
from journeys.utils.device import Device

JOURNEYS_PRETTY_FORM_TEXTS = {
    "type_changes": "Type of {diff_path} changed from {type_t1} to {type_t2} and "
    "value changed from {val_t1} to {val_t2}.",
    "values_changed": "{diff_path} changed from {val_t1} to {val_t2}.",
    "dictionary_item_added": "{diff_path} added to {collection_name}.",
    "dictionary_item_removed": "{diff_path} removed from {collection_name}.",
    "iterable_item_added": "{diff_path} added to {collection_name}.",
    "iterable_item_removed": "{diff_path} removed from {collection_name}.",
    "attribute_added": "Attribute of {diff_path} added.",
    "attribute_removed": "Attribute of {diff_path} removed.",
    "set_item_added": "[{val_t2}] added to set in {collection_name}",
    "set_item_removed": "[{val_t1}] removed from set in {collection_name}.",
    "repetition_change": "Repetition change for {diff_path} in {collection_name}.",
}


def convert_raw_to_dict(raw_obj) -> dict:
    """Apply change operations to raw object from iControl lib.
    - remove keys starting with '_'.
    - remove self links that always changes between versions.
    """
    ret_dict = {}
    for key, value in raw_obj.items():
        if not key.startswith("_") and key != "selfLink":
            ret_dict[key] = value
    return ret_dict


def pretty(diff: DeepDiff, root: str, collection_name: str, pretty_form_texts=None):
    if pretty_form_texts is None:
        pretty_form_texts = JOURNEYS_PRETTY_FORM_TEXTS
    result = []
    keys = sorted(
        diff.tree.keys()
    )  # sorting keys to guarantee constant order across python
    # versions.
    for key in keys:
        for item_key in diff.tree[key]:
            result += [
                _pretty_print_diff(item_key, root, collection_name, pretty_form_texts)
            ]

    return "\n".join(result)


def _get_pretty_format_args(diff, root):
    type_t1 = get_type(diff.t1).__name__
    type_t2 = get_type(diff.t2).__name__
    val_t1 = '"{}"'.format(str(diff.t1)) if type_t1 == "str" else str(diff.t1)
    val_t2 = '"{}"'.format(str(diff.t2)) if type_t2 == "str" else str(diff.t2)
    diff_path = diff.path(root)
    return diff_path, type_t1, type_t2, val_t1, val_t2


def _pretty_print_diff(diff, root, collection_name, pretty_form_texts: Dict):
    diff_path, type_t1, type_t2, val_t1, val_t2 = _get_pretty_format_args(diff, root)
    return pretty_form_texts.get(diff.report_type, "").format(
        diff_path=diff_path,
        type_t1=type_t1,
        type_t2=type_t2,
        val_t1=val_t1,
        val_t2=val_t2,
        collection_name=collection_name,
    )


def tmsh_compare(cmd: str, first: Device, second: Device) -> str:
    """Get unified diff from tmsh command executed on 2 devices."""
    if not cmd.startswith("tmsh "):
        raise InputError
    diff = unified_diff(
        *[
            device.ssh.run(cmd).stdout.splitlines(keepends=True)
            for device in (first, second)
        ]
    )
    return "".join(diff)
