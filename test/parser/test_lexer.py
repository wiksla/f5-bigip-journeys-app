import pytest

from journeys.parser.errors import ParserSyntaxError

from .configs import lex_config


def test_lexer():
    tokens = lex_config("with_comments/simple_comments.conf")
    assert tokens == [
        ("# Very important config note", 1),
        ("ltm", 2),
        ("virtual", 2),
        ("/Common/EXPLICIT-PROXY-HTTPS-BYPASS", 2),
        ("{", 2),
        ("\n", 3),
        ("destination", 3),
        ("/Common/0.0.0.0:443", 3),
        ("\n", 4),
        ("profiles", 4),
        ("{", 4),
        ("\n", 5),
        ("/Common/tcp", 5),
        ("{", 5),
        ("}", 5),
        ("\n", 6),
        ("}", 6),
        ("\n", 7),
        ("translate-address", 7),
        ("disabled", 7),
        ("\n", 8),
        ("# very important internal note", 8),
        ("vlans", 9),
        ("{", 9),
        ("\n", 10),
        ("/Common/tcp-forward-tunnel", 10),
        ("\n", 11),
        ("}", 11),
        ("\n", 12),
        ("vlans-enabled", 12),
        ("\n", 13),
        ("}", 13),
        ("\n", 14),
    ]


def test_not_balanced_brackets():
    with pytest.raises(ParserSyntaxError):
        lex_config("not_balanced/not_balanced_brackets.conf")
