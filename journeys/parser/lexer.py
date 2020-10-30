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


import itertools
from collections import deque

from .compat import fix_pep_479
from .const import BLOBTYPES
from .const import MODULES
from .errors import ParserSyntaxError


class _LookaheadIterator:
    def __init__(self, iterable, buffer_size=10):
        self.iter = iterable
        self.size = buffer_size
        self.buffer = deque()
        self.update_buffer()

    def update_buffer(self):
        try:
            while len(self.buffer) < self.size:
                self.buffer.append(next(self.iter))
        except StopIteration:
            pass

    def __iter__(self):
        return self

    def __next__(self):
        try:
            val = self.buffer.popleft()
            self.update_buffer()
            return val
        except IndexError:
            raise StopIteration


@fix_pep_479
def _iterescape(iterable):
    chars = iter(iterable)
    for char in chars:
        if char == "\\":
            char = char + next(chars)
        yield char


def _iterlinecount(iterable):
    line = 1
    chars = iter(iterable)
    for char in chars:
        if char.endswith("\n"):
            line += 1
        yield (char, line)


@fix_pep_479
def _lex_file_object(iterable):
    """
    Generates token tuples from a config file object

    Yields 3-tuples like (token, lineno, quoted)
    """
    token = ""  # the token buffer
    token_line = 0  # the line the token starts on
    full_field = []
    blob = False

    # prepare substrings for blobs / modules matching
    # append a space to each to avoid capturing word parts
    blobtypes = tuple(" ".join(args) + " " for args in BLOBTYPES)
    modules = tuple(f"{module} " for module in MODULES)

    it = itertools.chain.from_iterable(iterable)
    it = _iterescape(it)  # treat escaped characters differently
    it = _LookaheadIterator(it)  # allow us to look up the next sequence of characters
    it_lines = _iterlinecount(it)  # count the number of newline characters

    for char, line in it_lines:
        # if blob mode, just append all the coming chars into a single token
        # until an exit condition happens
        if blob:
            token += char
            if (char == "\n" and "".join(it.buffer).startswith(modules)) or len(
                it.buffer
            ) == 0:
                blob = False
                # find the last occurence of a closing brace, ensure it's not inside a comment
                # (will consume any comments inbetween)
                brace_index = token.rfind("}")
                token = token[:brace_index]
                while "#" in token[token.rfind("\n") :]:
                    brace_index = token.rfind("}")
                    token = token[:brace_index]
                yield token, token_line, False
                yield "}", line, False
                yield "\n", line, False
                token = ""
            continue

        # handle whitespace
        if char.isspace():
            # if token complete yield it and reset token buffer
            if token:
                yield (token, token_line, False)
                full_field.append(token)
                token = ""

            # disregard until char isn't a whitespace character, keep newlines
            while char.isspace():
                if char == "\n":
                    yield (char, line, False)
                    full_field = []
                char, line = next(it_lines)

        # if starting comment
        if not token and char == "#":
            while not char.endswith("\n"):
                token = token + char
                char, _ = next(it_lines)
            yield (token, line, False)
            token = ""
            full_field = []
            continue

        if not token:
            token_line = line

        # if a quote is found, add the whole string to the token buffer
        if char in ('"', "'"):

            quote = char
            char, line = next(it_lines)
            while char != quote:
                token += quote if char == "\\" + quote else char
                char, line = next(it_lines)

            yield (token, token_line, True)  # True because this is in quotes

            token = ""
            continue

        # handle special characters that are treated like full tokens
        if char in ("{", "}"):
            # if token complete yield it and reset token buffer
            if token:
                yield (token, token_line, False)
                token = ""

            # this character is a full token so yield it now
            yield (char, line, False)

            if char == "{" and " ".join(full_field).startswith(blobtypes):
                blob = True
            full_field = []
            continue

        # append char to the token buffer
        token += char


def _balance_braces(tokens, filename=None):
    """Raises syntax errors if braces aren't balanced"""
    depth = 0

    for token, line, quoted in tokens:
        if token == "}" and not quoted:
            depth -= 1
        elif token == "{" and not quoted:
            depth += 1

        # raise error if we ever have more right braces than left
        if depth < 0:
            reason = 'unexpected "}"'
            raise ParserSyntaxError(reason, filename, line)
        else:
            yield (token, line, quoted)

    # raise error if we have less right braces than left at EOF
    if depth > 0:
        reason = 'unexpected end of file, expecting "}"'
        raise ParserSyntaxError(reason, filename, line)


def lex(iterable):
    """Generates tokens from a config file"""
    it = _lex_file_object(iterable)
    it = _balance_braces(it)
    for token, line, quoted in it:
        yield (token, line, quoted)
