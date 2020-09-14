# -*- coding: utf-8 -*-
import codecs
import os

from .const import BLOBTYPES
from .const import LISTTYPES

DELIMITERS = ("{", "}", ";")


def _escape(string):
    prev, char = "", ""
    for char in string:
        if prev == "\\":
            prev += char
            yield prev
            continue
        if char != "\\":
            yield char
        prev = char
    if char == "\\":
        yield char


def _needs_quotes(string):
    if string == "":
        return True
    if string == "#":
        return False

    # lexer should throw an error when variable expansion syntax
    # is messed up, but just wrap it in quotes for now I guess
    chars = _escape(string)

    # arguments can't start with variable expansion syntax
    char = next(chars)
    if char.isspace() or char in ("{", "}", ";", '"', "'", "#", "|"):
        return True

    expanding = False
    for char in chars:
        if char.isspace() or char in ("{", ";", '"', "'", "#", "|"):
            return True

    return char in ("\\", "$") or expanding


def _enquote(arg):
    if not _needs_quotes(arg):
        return arg
    return '"' + arg.replace('"', '\\"') + '"'


def build(payload, indent=4, tabs=False, header=False):
    padding = "\t" if tabs else " " * indent

    head = ""
    if header:
        head += "# Built by journeys app.\n"
        head += "\n"

    def _build_blob(output, block):
        # blobs will always have len = 1 and be stored in first arg index
        blob = block[0]["args"][0]
        output += blob
        return output

    def _build_block(output, block, depth, current_object=None, newlines=True):
        margin = padding * depth

        for stmt in block:
            try:
                directive = _enquote(stmt["args"][0])
            except IndexError:
                directive = ""

            if directive == "#":
                built = "#" + stmt["comment"]
            else:
                args = [_enquote(arg) for arg in stmt["args"]]

                built = " ".join(args)

                if stmt.get("block") is not None:
                    if built:
                        built += " "
                    built += "{"
                    if (
                        depth == 0 and tuple(stmt["args"][:-1]) in BLOBTYPES
                    ):  # ignore last arg - all blob types have a name
                        built = _build_blob(built, stmt["block"])
                    else:
                        base_obj = " ".join(args) if depth == 0 else current_object
                        is_list = False
                        if current_object:
                            list_fields = next(
                                (
                                    v
                                    for k, v in LISTTYPES.items()
                                    if current_object.startswith(k)
                                ),
                                None,
                            )
                            if list_fields and "".join(args).startswith(list_fields):
                                is_list = True
                                built += " "
                        built = _build_block(
                            built,
                            stmt["block"],
                            depth + 1,
                            base_obj,
                            newlines=not is_list,
                        )
                        if not stmt.get("block") or is_list:
                            built = built + " "
                        else:
                            built += "\n" + margin
                    built += "}"
                if stmt.get("comment") is not None:
                    built += " #" + stmt["comment"]

            output += ("\n" + margin if output and newlines else "") + built

        return output

    body = ""
    body = _build_block(body, payload, 0)
    return head + body


def build_files(payload, dirname=None, indent=4, tabs=False, header=False, files=None):
    """
    Uses a full config payload (output of parser.parse) to build
    config files, then writes those files to disk.
    """
    if dirname is None:
        dirname = os.getcwd()

    for config in payload["config"]:
        path = config["file"]

        if files and path not in files:
            continue

        if not os.path.isabs(path):
            path = os.path.join(dirname, path)

        # make directories that need to be made for the config to be built
        dirpath = os.path.dirname(path)
        if not os.path.exists(dirpath):
            os.makedirs(dirpath)

        parsed = config["parsed"]
        output = build(parsed, indent=indent, tabs=tabs, header=header)
        output = output.rstrip() + "\n"
        with codecs.open(path, "w", encoding="utf-8") as fp:
            fp.write(output)
