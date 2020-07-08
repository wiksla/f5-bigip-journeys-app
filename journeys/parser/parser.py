# -*- coding: utf-8 -*-

from .analyzer import enter_block_ctx
from .const import NONAME
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
    Parses an nginx config file and returns a nested dict payload

    :param iterable: object from which we can read the subsequent characters
    :param filename: identifier for the file, saved in the output json
    :param onerror: function that determines what's saved in "callback"
    :param catch_errors: bool; if False, parse stops after first error
    :param ignore: list or tuple of directives to exclude from the payload
    :param comments: bool; if True, including comments to json payload
    :param strict: bool; if True, unrecognized directives raise errors
    :param check_ctx: bool; if True, runs context analysis on directives
    :param check_args: bool; if True, runs arg count analysis on directives
    :returns: a payload that describes the parsed nginx config
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
        """Recursively parses nginx config contexts"""
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

            stmt = {"directive": directive, "line": lineno, "args": []}

            # if token is comment
            if directive.startswith("#") and not quoted:
                if comments:
                    stmt["directive"] = "#"
                    stmt["comment"] = token[1:]
                    parsed.append(stmt)
                continue

            # unnamed block - do not consume the token, instead assign a fake directive '_unnamed'
            if directive == "{":
                stmt["directive"] = "_unnamed"
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
            if stmt["directive"] in ignore:
                # if this directive was a block consume it too
                if token == "{" and not quoted:
                    _parse(parsing, tokens, consume=True)
                continue

            # if this statement terminated with '{' then it is a block
            if token == "{" and not quoted:
                inner = enter_block_ctx(stmt, ctx)  # get context for block
                stmt["block"] = _parse(parsing, tokens, ctx=inner)

            _assign_type_and_name(stmt=stmt, ctx=ctx)
            parsed.append(stmt)

            # add all comments found inside args after stmt is added
            for comment in comments_in_args:
                comment_stmt = {
                    "directive": "#",
                    "line": stmt["line"],
                    "args": [],
                    "comment": comment,
                }
                parsed.append(comment_stmt)

            # do not iterate further if we've encountered a closing brace right after the directive
            if token == "}" and not quoted:
                break

        return parsed

    def _assign_type_and_name(stmt, ctx):
        """Assigns a type and name for statement"""
        if ctx == ():
            directive = stmt["directive"]
            args = stmt["args"]
            if (directive in NONAME and args in NONAME[directive]) or len(args) == 1:
                type_ = " ".join(args)
                name = None
            else:
                type_ = " ".join(args[:-1])
                name = args[-1]
            stmt["type"] = type_
            stmt["name"] = name

    tokens = lex(iterable)
    parsing = {"file": filename, "status": "ok", "errors": [], "parsed": []}
    try:
        parsing["parsed"] = _parse(parsing, tokens, ctx=())
    except Exception as e:
        _handle_error(parsing, e)

    payload["config"].append(parsing)

    return payload
