# -*- coding: utf-8 -*-

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

from pathlib import Path

from .lexer import lex


def parse(
    iterable,
    filename="unnamed",
    onerror=None,
    catch_errors=True,
    ignore=(),
    comments=True,
    strict=False,
    check_ctx=True,
    check_args=True,
):
    """
    Parses a config file and returns a nested dict payload

    :param iterable: object from which we can read the subsequent characters
    :param filename: identifier for the file, saved in the output json
    :param onerror: function that determines what's saved in "callback"
    :param catch_errors: bool; if False, parse stops after first error
    :param ignore: list or tuple of directives to exclude from the payload
    :param comments: bool; if True, including comments to json payload
    :param strict: bool; if True, unrecognized directives raise errors
    :param check_ctx: bool; if True, runs context analysis on directives
    :param check_args: bool; if True, runs arg count analysis on directives
    :returns: a payload that describes the parsed config
    """

    payload = {
        "status": "ok",
        "errors": [],
        "config": [],
    }

    def _handle_error(parsing, e):
        """Adds representaions of an error to the payload"""
        file = parsing["file"]
        error = str(e)
        line = getattr(e, "lineno", None)

        parsing_error = {"error": error, "line": line}
        payload_error = {"file": file, "error": error, "line": line}
        if onerror is not None:
            payload_error["callback"] = onerror(e)

        parsing["status"] = "failed"
        parsing["errors"].append(parsing_error)

        payload["status"] = "failed"
        payload["errors"].append(payload_error)

    def _parse(parsing, tokens, ctx=(), consume=False):
        """Recursively parse config contexts"""
        parsed = []

        # parse recursively by pulling from a flat stream of tokens
        for token, lineno, quoted in tokens:
            comments_in_args = []

            # we are parsing a block, so break if it's closing
            if token == "}" and not quoted:
                break

            # if we are consuming, then just continue until end of context
            if consume:
                # if we find a block inside this context, consume it too
                if token == "{" and not quoted:
                    _parse(parsing, tokens, consume=True)
                continue

            # skip newlines if we haven't started working on a directive yet
            if token == "\n":
                continue

            directive = token

            stmt = {"line": lineno, "args": [directive]}

            # if token is comment
            if directive.startswith("#") and not quoted:
                if comments:
                    stmt["args"][0] = "#"
                    stmt["comment"] = token[1:]
                    parsed.append(stmt)
                continue

            # unnamed block - do not consume the token, instead assign a fake directive '_unnamed'
            if directive == "{":
                stmt["args"].remove(directive)
            else:
                token, __, quoted = next(tokens)  # disregard line numbers of args

            # TODO: add external scf_tool checking and handling

            # parse arguments by reading tokens
            while token not in ("{", "\n", "}") or quoted:
                if token.startswith("#") and not quoted:
                    comments_in_args.append(token[1:])
                else:
                    stmt["args"].append(token)

                token, __, quoted = next(tokens)

            # consume the directive if it is ignored and move on
            if directive in ignore:
                # if this directive was a block consume it too
                if token == "{" and not quoted:
                    _parse(parsing, tokens, consume=True)
                continue

            # if this statement terminated with '{' then it is a block
            if token == "{" and not quoted:
                inner = ctx + (directive,)  # set context for block
                stmt["block"] = _parse(parsing, tokens, ctx=inner)

            # _assign_type_and_name(stmt=stmt, ctx=ctx)
            parsed.append(stmt)

            # add all comments found inside args after stmt is added
            for comment in comments_in_args:
                comment_stmt = {
                    "line": stmt["line"],
                    "args": ["#"],
                    "comment": comment,
                }
                parsed.append(comment_stmt)

            # do not iterate further if we've encountered a closing brace right after the directive
            if token == "}" and not quoted:
                break

        return parsed

    tokens = lex(iterable)
    parsing = {"file": filename, "status": "ok", "errors": [], "parsed": []}
    try:
        parsing["parsed"] = _parse(parsing, tokens, ctx=())
    except Exception as e:
        _handle_error(parsing, e)

    payload["config"].append(parsing)

    return payload


def parse_dir(dirname, **kwargs):
    conf_path = Path(dirname)
    payload = {
        "status": "ok",
        "errors": [],
        "config": [],
    }

    files_to_parse = []

    for _file in [
        "bigip.conf",
        "bigip_base.conf",
        "bigip_gtm.conf",
        "bigip_script.conf",
        "bigip_user.conf",
        "profile_base.conf",
        "low_profile_base.conf",
        "cipher.conf",
        "daemon.conf",
    ]:
        files_to_parse.extend(conf_path.glob(_file))
        files_to_parse.extend(conf_path.glob("partitions/*/" + _file))

    for path in files_to_parse:
        with open(path, "r") as f:
            conf = parse(f, str(path.relative_to(conf_path)), **kwargs)
        payload["config"].extend(conf["config"])
        if conf["status"] == "failed":
            payload["status"] = "failed"
            payload["errors"].extend(conf["errors"])

    return payload
