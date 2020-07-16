# -*- coding: utf-8 -*-
import codecs
import os
import re

from .const import BLOBTYPES

DELIMITERS = ("{", "}", ";")
ESCAPE_SEQUENCES_RE = re.compile(r"(\\x[0-9a-f]{2}|\\[0-7]{1,3})")


def _escape(string):
    prev, char = "", ""
    for char in string:
        if prev == "\\" or prev + char == "${":
            prev += char
            yield prev
            continue
        if prev == "$":
            yield prev
        if char not in ("\\", "$"):
            yield char
        prev = char
    if char in ("\\", "$"):
        yield char


def _needs_quotes(string):
    if string == "":
        return True

    # lexer should throw an error when variable expansion syntax
    # is messed up, but just wrap it in quotes for now I guess
    chars = _escape(string)

    # arguments can't start with variable expansion syntax
    char = next(chars)
    if char.isspace() or char in ("{", "}", ";", '"', "'", "${"):
        return True

    expanding = False
    for char in chars:
        if char.isspace() or char in ("{", ";", '"', "'"):
            return True
        elif char == ("${" if expanding else "}"):
            return True
        elif char == ("}" if expanding else "${"):
            expanding = not expanding

    return char in ("\\", "$") or expanding


def _replace_escape_sequences(match):
    return match.group(1).decode("string-escape")


def _enquote(arg):
    if not _needs_quotes(arg):
        return arg
    return repr(arg).replace("\\\\", "\\")


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

    def _build_block(output, block, depth):
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
                        built = _build_block(built, stmt["block"], depth + 1)
                        if not stmt.get("block"):
                            built += " "
                        else:
                            built += "\n" + margin
                    built += "}"
                if stmt.get("comment") is not None:
                    built += " #" + stmt["comment"]

            output += ("\n" if output else "") + margin + built

        return output

    body = ""
    body = _build_block(body, payload, 0)
    return head + body


def build_files(payload, dirname=None, indent=4, tabs=False, header=False):
    """
    Uses a full config payload (output of parser.parse) to build
    config files, then writes those files to disk.
    """
    if dirname is None:
        dirname = os.getcwd()

    for config in payload["config"]:
        path = config["file"]
        if not os.path.isabs(path):
            path = os.path.join(dirname, path)

        # make directories that need to be made for the config to be built
        dirpath = os.path.dirname(path)
        if not os.path.exists(dirpath):
            os.makedirs(dirpath)

        # build then create the config file using the json payload
        parsed = config["parsed"]
        output = build(parsed, indent=indent, tabs=tabs, header=header)
        output = output.rstrip() + "\n"
        with codecs.open(path, "w", encoding="utf-8") as fp:
            fp.write(output)
