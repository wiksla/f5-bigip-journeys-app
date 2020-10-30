"""
Copyright 2020 F5 Networks Inc.

Copyright 2018 NGINX, Inc.

Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at

 http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.

This file has been modified by F5 Networks Inc. for the purpose of adding support for processing bigip config files.
"""


import io
import json
import os
import sys
from traceback import format_exception

from .builder import build as build_string
from .builder import build_files
from .lexer import lex as lex_file
from .parser import parse as parse_file


def _prompt_yes():
    try:
        return input("overwrite? (y/n [n]) ").lower().startswith("y")
    except (KeyboardInterrupt, EOFError):
        sys.exit(1)


def _dump_payload(obj, fp, indent):
    kwargs = {"indent": indent}
    if indent is None:
        kwargs["separators"] = ",", ":"
    fp.write(json.dumps(obj, **kwargs) + u"\n")


def parse(
    filename,
    out,
    indent=None,
    catch=None,
    tb_onerror=None,
    ignore="",
    comments=True,
    strict=False,
):

    ignore = ignore.split(",") if ignore else []

    def callback(e):
        exc = sys.exc_info() + (10,)
        return "".join(format_exception(*exc)).rstrip()

    kwargs = {
        "catch_errors": catch,
        "ignore": ignore,
        "comments": comments,
        "strict": strict,
    }

    if tb_onerror:
        kwargs["onerror"] = callback

    with open(filename, "r") as f:
        payload = parse_file(f, filename, **kwargs)
    o = sys.stdout if out is None else io.open(out, "w", encoding="utf-8")
    try:
        _dump_payload(payload, o, indent=indent)
    finally:
        o.close()


def build(
    filename,
    dirname=None,
    force=False,
    indent=4,
    tabs=False,
    header=False,
    stdout=False,
    verbose=False,
):

    if dirname is None:
        dirname = os.getcwd()

    # read the json payload from the specified file
    with open(filename, "r") as fp:
        payload = json.load(fp)

    # find which files from the json payload will overwrite existing files
    if not force and not stdout:
        existing = []
        for config in payload["config"]:
            path = config["file"]
            if not os.path.isabs(path):
                path = os.path.join(dirname, path)
            if os.path.exists(path):
                existing.append(path)
        # ask the user if it's okay to overwrite existing files
        if existing:
            print("building {} would overwrite these files:".format(filename))
            print("\n".join(existing))
            if not _prompt_yes():
                print("not overwritten")
                return

    # if stdout is set then just print each file after another
    if stdout:
        for config in payload["config"]:
            path = config["file"]
            if not os.path.isabs(path):
                path = os.path.join(dirname, path)
            parsed = config["parsed"]
            output = build_string(parsed, indent=indent, tabs=tabs, header=header)
            output = output.rstrip() + "\n"
            print("# " + path + "\n" + output)
        return

    # build the configuration file from the json payload
    build_files(payload, dirname=dirname, indent=indent, tabs=tabs, header=header)

    # if verbose print the paths of the config files that were created
    if verbose:
        for config in payload["config"]:
            path = config["file"]
            if not os.path.isabs(path):
                path = os.path.join(dirname, path)
            print("wrote to " + path)


def lex(filename, out=False, indent=None, line_numbers=False):
    payload = list(lex_file(filename))
    if line_numbers:
        payload = [(token, lineno) for token, lineno, quoted in payload]
    else:
        payload = [token for token, lineno, quoted in payload]

    if not out:
        return payload
    else:
        o = io.open(out, "w", encoding="utf-8")
        try:
            _dump_payload(payload, o, indent=indent)
        finally:
            o.close()
