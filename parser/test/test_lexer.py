# -*- coding: utf-8 -*-
import os

import parser
from . import here


def test_simple_config():
    dirname = os.path.join(here, 'configs', 'simple')
    config = os.path.join(dirname, 'nginx.conf')
    tokens = parser.lex(config)
    assert list((token, line) for token, line, quoted in tokens) == [
        ('events', 1), ('{', 1), ('worker_connections', 2), ('1024', 2),
        (';', 2), ('}', 3), ('http', 5), ('{', 5), ('server', 6), ('{', 6),
        ('listen', 7), ('127.0.0.1:8080', 7), (';', 7), ('server_name', 8),
        ('default_server', 8), (';', 8), ('location', 9), ('/', 9), ('{', 9),
        ('return', 10), ('200', 10), ('foo bar baz', 10), (';', 10), ('}', 11),
        ('}', 12), ('}', 13)
    ]


def test_with_config_comments():
    dirname = os.path.join(here, 'configs', 'with-comments')
    config = os.path.join(dirname, 'nginx.conf')
    tokens = parser.lex(config)
    assert list((token, line) for token, line, quoted in tokens) == [
        ('events', 1), ('{', 1), ('worker_connections', 2), ('1024', 2),
        (';', 2), ('}', 3),('#comment', 4), ('http', 5), ('{', 5),
        ('server', 6), ('{', 6), ('listen', 7), ('127.0.0.1:8080', 7),
        (';', 7), ('#listen', 7), ('server_name', 8),
        ('default_server', 8),(';', 8), ('location', 9), ('/', 9),
        ('{', 9), ('## this is brace', 9), ('# location /', 10), ('return', 11), ('200', 11),
        ('foo bar baz', 11), (';', 11), ('}', 12), ('}', 13), ('}', 14)
    ]


def test_quote_behavior():
    dirname = os.path.join(here, 'configs', 'quote-behavior')
    config = os.path.join(dirname, 'nginx.conf')
    tokens = parser.lex(config)
    assert list(token for token, line, quoted in tokens) == [
        'outer-quote', 'left', '-quote', 'right-"quote"', 'inner"-"quote', ';',
        '', '', 'left-empty', 'right-empty""', 'inner""empty', 'right-empty-single"', ';',
    ]


def test_quoted_right_brace():
    dirname = os.path.join(here, 'configs', 'quoted-right-brace')
    config = os.path.join(dirname, 'nginx.conf')
    tokens = parser.lex(config)
    assert list(token for token, line, quoted in tokens) == [
        'events', '{', '}', 'http', '{', 'log_format', 'main', 'escape=json',
        '{ "@timestamp": "$time_iso8601", ', '"server_name": "$server_name", ',
        '"host": "$host", ', '"status": "$status", ',
        '"request": "$request", ', '"uri": "$uri", ', '"args": "$args", ',
        '"https": "$https", ', '"request_method": "$request_method", ',
        '"referer": "$http_referer", ', '"agent": "$http_user_agent"', '}',
        ';', '}'
    ]
