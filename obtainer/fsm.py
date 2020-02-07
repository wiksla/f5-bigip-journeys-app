import string

from enum import Enum
from itertools import chain


class State(Enum):
    START = 0
    COMMENT = 1
    CMD = 2
    BODY = 3
    BODY_Q = 4


WHITE = string.whitespace
NEW_LINE = "\n"
COMMENT_OPEN = "#"
COMMENT_CLOSE = NEW_LINE
BODY_OPEN = "{"
BODY_CLOSE = "}"
BODY_Q_OPEN = '"'
BODY_Q_CLOSE = '"'
CMD_DISALLOWED = COMMENT_OPEN + COMMENT_CLOSE + BODY_CLOSE


class ParsingError(Exception):
    """ FSM finished in different state than START or COMMENT. """


def parse(config):
    for cmd, body in sanitize(config):
        yield cmd, body


def sanitize(config):
    """
    Simple FSM (Finite State Machine) for
    parsing scf format: bigip.conf / bigip_base.conf / gtm.conf

    Example usage:
        inp = open('/home/mj/config/bigip_base.conf')
        for cmd, body in parse(config=inp):
            print('{}: {}'.format(cmd, body))
        inp.close()
    """

    current_line = 1
    current_col = 1

    current_cmd = []
    current_body = []
    body_level = 0

    current_state = State.START

    def parsing_err():
        raise ParsingError(
            "{}, ch '{}', ln {}:{}".format(current_state, ch, current_line, current_col)
        )

    for ch in chain.from_iterable(config):
        if ch in NEW_LINE:
            current_line += 1
            current_col = 1
        else:
            current_col += 1

        if current_state == State.START:
            if ch in WHITE:
                continue
            if ch in COMMENT_OPEN:
                current_state = State.COMMENT
                continue
            current_state = State.CMD
            current_cmd.append(ch)
            continue

        if current_state == State.BODY:

            if ch in BODY_CLOSE:
                body_level -= 1

                if body_level == 0:
                    current_state = State.START
                    yield ("".join(current_cmd).strip(), "".join(current_body).strip())
                    current_cmd, current_body = [], []
                    continue

                current_body.append(ch)
                continue
            if ch in BODY_OPEN:
                body_level += 1
                current_body.append(ch)
                continue
            if ch in BODY_Q_OPEN:
                current_state = State.BODY_Q
                current_body.append(ch)
                continue

            if ch in COMMENT_OPEN:
                current_state = State.COMMENT
                continue

            current_body.append(ch)
            continue

        if current_state == State.CMD:
            if ch in BODY_OPEN:
                body_level += 1
                current_state = State.BODY
                continue
            if ch in CMD_DISALLOWED:
                parsing_err()
            current_cmd.append(ch)
            continue

        if current_state == State.BODY_Q:
            if ch in BODY_Q_CLOSE:
                current_state = State.BODY
            current_body.append(ch)
            continue

        if current_state == State.COMMENT:
            if ch in COMMENT_CLOSE and body_level > 0:
                current_state = State.BODY
                continue

            if ch in COMMENT_CLOSE:
                current_state = State.START
            continue

    if current_state not in (State.START, State.COMMENT):
        parsing_err()
