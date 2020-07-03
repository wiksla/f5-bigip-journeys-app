# -*- coding: utf-8 -*-
import io
import itertools
from collections import deque

from .compat import fix_pep_479
from .errors import NgxParserSyntaxError

EXTERNAL_LEXERS = {}

BLOBTYPES = (
    "ltm rule ",
    "gtm rule ",
    "sys application apl-script ",
    "sys application template ",
    "sys icall script ",
    "cli script ",
)
MODULES = (
    "analytics ",
    "apm ",
    "asm ",
    "auth ",
    "cli ",
    "gtm ",
    "ilx ",
    "ltm ",
    "net ",
    "pem ",
    "security ",
    "sys ",
    "vcmp ",
    "wam ",
    "wom ",
)


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
def _lex_file_object(file_obj):
    """
    Generates token tuples from an nginx config file object

    Yields 3-tuples like (token, lineno, quoted)
    """
    token = ""  # the token buffer
    token_line = 0  # the line the token starts on
    next_token_is_directive = True
    full_field = []
    blob = False

    it = itertools.chain.from_iterable(file_obj)
    it = _iterescape(it)  # treat escaped characters differently
    it = _LookaheadIterator(it)  # allow us to look up the next sequence of characters
    it_lines = _iterlinecount(it)  # count the number of newline characters

    for char, line in it_lines:
        # if blob mode, just append all the coming chars into a single token
        # until an exit condition happens
        if blob:
            token += char
            if (char == "\n" and "".join(it.buffer).startswith(MODULES)) or len(
                it.buffer
            ) == 0:
                blob = False
                # find the last occurence of a closing brace
                # (a commented block here with a closing brace inside will break this..)
                # (will consume any comments inbetween)
                brace_index = token.rfind("}")
                token = token[:brace_index]
                yield token, token_line, False
                yield "}", line, False
                yield "\n", line, False
                token = ""
                next_token_is_directive = True
            continue

        # handle whitespace
        if char.isspace():
            # if token complete yield it and reset token buffer
            if token:
                yield (token, token_line, False)
                full_field.append(token)
                if next_token_is_directive and token in EXTERNAL_LEXERS:
                    for custom_lexer_token in EXTERNAL_LEXERS[token](it_lines, token):
                        yield custom_lexer_token
                        next_token_is_directive = True
                else:
                    next_token_is_directive = False
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
            # if a quote is inside a token, treat it like any other char
            # if token:
            #     token += char
            #     continue

            quote = char
            char, line = next(it_lines)
            while char != quote:
                token += quote if char == "\\" + quote else char
                char, line = next(it_lines)

            yield (token, token_line, True)  # True because this is in quotes

            # handle quoted external directives
            if next_token_is_directive and token in EXTERNAL_LEXERS:
                for custom_lexer_token in EXTERNAL_LEXERS[token](it_lines, token):
                    yield custom_lexer_token
                    next_token_is_directive = True
            else:
                next_token_is_directive = False

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

            if char == "{" and " ".join(full_field).startswith(BLOBTYPES):
                blob = True
            else:
                next_token_is_directive = True
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
            raise NgxParserSyntaxError(reason, filename, line)
        else:
            yield (token, line, quoted)

    # raise error if we have less right braces than left at EOF
    if depth > 0:
        reason = 'unexpected end of file, expecting "}"'
        raise NgxParserSyntaxError(reason, filename, line)


def lex(filename):
    """Generates tokens from an nginx config file"""
    with io.open(filename, mode="r", encoding="utf-8") as f:
        it = _lex_file_object(f)
        it = _balance_braces(it, filename)
        for token, line, quoted in it:
            yield (token, line, quoted)


def register_external_lexer(directives, lexer):
    for directive in directives:
        EXTERNAL_LEXERS[directive] = lexer
