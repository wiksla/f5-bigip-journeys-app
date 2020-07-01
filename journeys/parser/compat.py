# -*- coding: utf-8 -*-
import functools
import sys

PY3 = sys.version_info[0] == 3

input = input
basestring = str


def fix_pep_479(generator):
    """
    Python 3.7 breaks parser's lexer because of PEP 479
    Read more here: https://www.python.org/dev/peps/pep-0479/
    """

    @functools.wraps(generator)
    def _wrapped_generator(*args, **kwargs):
        try:
            for x in generator(*args, **kwargs):
                yield x
        except RuntimeError:
            return

    return _wrapped_generator
