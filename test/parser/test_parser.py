# -*- coding: utf-8 -*-
import os
import parser

from . import here


def test_ignore_directives():
    dirname = os.path.join(here, "configs", "simple")
    config = os.path.join(dirname, "nginx.conf")

    # check that you can ignore multiple directives
    payload = parser.parse(config, ignore=["listen", "server_name"])
    assert payload == {
        "status": "ok",
        "errors": [],
        "config": [
            {
                "file": os.path.join(dirname, "nginx.conf"),
                "status": "ok",
                "errors": [],
                "parsed": [
                    {
                        "directive": "events",
                        "line": 1,
                        "args": [],
                        "block": [
                            {
                                "directive": "worker_connections",
                                "line": 2,
                                "args": ["1024"],
                            }
                        ],
                    },
                    {
                        "directive": "http",
                        "line": 5,
                        "args": [],
                        "block": [
                            {
                                "directive": "server",
                                "line": 6,
                                "args": [],
                                "block": [
                                    {
                                        "directive": "location",
                                        "line": 9,
                                        "args": ["/"],
                                        "block": [
                                            {
                                                "directive": "return",
                                                "line": 10,
                                                "args": ["200", "foo bar baz"],
                                            }
                                        ],
                                    }
                                ],
                            }
                        ],
                    },
                ],
            }
        ],
    }

    # check that you can also ignore block directives
    payload = parser.parse(config, ignore=["events", "server"])
    assert payload == {
        "status": "ok",
        "errors": [],
        "config": [
            {
                "file": os.path.join(dirname, "nginx.conf"),
                "status": "ok",
                "errors": [],
                "parsed": [{"directive": "http", "line": 5, "args": [], "block": []}],
            }
        ],
    }


def test_config_with_comments():
    dirname = os.path.join(here, "configs", "with-comments")
    config = os.path.join(dirname, "nginx.conf")
    payload = parser.parse(config, comments=True)
    assert payload == {
        "errors": [],
        "status": "ok",
        "config": [
            {
                "errors": [],
                "parsed": [
                    {
                        "block": [
                            {
                                "directive": "worker_connections",
                                "args": ["1024"],
                                "line": 2,
                            }
                        ],
                        "line": 1,
                        "args": [],
                        "directive": "events",
                    },
                    {"line": 4, "directive": "#", "args": [], "comment": "comment"},
                    {
                        "block": [
                            {
                                "args": [],
                                "directive": "server",
                                "line": 6,
                                "block": [
                                    {
                                        "args": ["127.0.0.1:8080"],
                                        "directive": "listen",
                                        "line": 7,
                                    },
                                    {
                                        "args": [],
                                        "directive": "#",
                                        "comment": "listen",
                                        "line": 7,
                                    },
                                    {
                                        "args": ["default_server"],
                                        "directive": "server_name",
                                        "line": 8,
                                    },
                                    {
                                        "block": [
                                            {
                                                "args": [],
                                                "directive": "#",
                                                "line": 9,
                                                "comment": "# this is brace",
                                            },
                                            {
                                                "args": [],
                                                "directive": "#",
                                                "line": 10,
                                                "comment": " location /",
                                            },
                                            {
                                                "line": 11,
                                                "directive": "return",
                                                "args": ["200", "foo bar baz"],
                                            },
                                        ],
                                        "line": 9,
                                        "directive": "location",
                                        "args": ["/"],
                                    },
                                ],
                            }
                        ],
                        "line": 5,
                        "args": [],
                        "directive": "http",
                    },
                ],
                "status": "ok",
                "file": config,
            }
        ],
    }


def test_config_without_comments():
    dirname = os.path.join(here, "configs", "with-comments")
    config = os.path.join(dirname, "nginx.conf")
    payload = parser.parse(config, comments=False)
    assert payload == {
        "errors": [],
        "status": "ok",
        "config": [
            {
                "errors": [],
                "parsed": [
                    {
                        "block": [
                            {
                                "directive": "worker_connections",
                                "args": ["1024"],
                                "line": 2,
                            }
                        ],
                        "line": 1,
                        "args": [],
                        "directive": "events",
                    },
                    {
                        "block": [
                            {
                                "args": [],
                                "directive": "server",
                                "line": 6,
                                "block": [
                                    {
                                        "args": ["127.0.0.1:8080"],
                                        "directive": "listen",
                                        "line": 7,
                                    },
                                    {
                                        "args": ["default_server"],
                                        "directive": "server_name",
                                        "line": 8,
                                    },
                                    {
                                        "block": [
                                            {
                                                "line": 11,
                                                "directive": "return",
                                                "args": ["200", "foo bar baz"],
                                            }
                                        ],
                                        "line": 9,
                                        "directive": "location",
                                        "args": ["/"],
                                    },
                                ],
                            }
                        ],
                        "line": 5,
                        "args": [],
                        "directive": "http",
                    },
                ],
                "status": "ok",
                "file": os.path.join(dirname, "nginx.conf"),
            }
        ],
    }


def test_parse_strict():
    dirname = os.path.join(here, "configs", "spelling-mistake")
    config = os.path.join(dirname, "nginx.conf")
    payload = parser.parse(config, comments=True, strict=True)
    assert payload == {
        "status": "failed",
        "errors": [
            {
                "file": os.path.join(dirname, "nginx.conf"),
                "error": 'unknown directive "proxy_passs" in %s:7'
                % os.path.join(dirname, "nginx.conf"),
                "line": 7,
            }
        ],
        "config": [
            {
                "file": os.path.join(dirname, "nginx.conf"),
                "status": "failed",
                "errors": [
                    {
                        "error": 'unknown directive "proxy_passs" in %s:7'
                        % os.path.join(dirname, "nginx.conf"),
                        "line": 7,
                    }
                ],
                "parsed": [
                    {"directive": "events", "line": 1, "args": [], "block": []},
                    {
                        "directive": "http",
                        "line": 3,
                        "args": [],
                        "block": [
                            {
                                "directive": "server",
                                "line": 4,
                                "args": [],
                                "block": [
                                    {
                                        "directive": "location",
                                        "line": 5,
                                        "args": ["/"],
                                        "block": [
                                            {
                                                "directive": "#",
                                                "line": 6,
                                                "args": [],
                                                "comment": "directive is misspelled",
                                            }
                                        ],
                                    }
                                ],
                            }
                        ],
                    },
                ],
            }
        ],
    }


def test_parse_missing_semicolon():
    dirname = os.path.join(here, "configs", "missing-semicolon")

    # test correct error is raised when broken proxy_pass is in upper block
    above_config = os.path.join(dirname, "broken-above.conf")
    above_payload = parser.parse(above_config)
    assert above_payload == {
        "status": "failed",
        "errors": [
            {
                "file": above_config,
                "error": 'directive "proxy_pass" is not terminated by ";" in %s:4'
                % above_config,
                "line": 4,
            }
        ],
        "config": [
            {
                "file": above_config,
                "status": "failed",
                "errors": [
                    {
                        "error": 'directive "proxy_pass" is not terminated by ";" in %s:4'
                        % above_config,
                        "line": 4,
                    }
                ],
                "parsed": [
                    {
                        "directive": "http",
                        "line": 1,
                        "args": [],
                        "block": [
                            {
                                "directive": "server",
                                "line": 2,
                                "args": [],
                                "block": [
                                    {
                                        "directive": "location",
                                        "line": 3,
                                        "args": ["/is-broken"],
                                        "block": [],
                                    },
                                    {
                                        "directive": "location",
                                        "line": 6,
                                        "args": ["/not-broken"],
                                        "block": [
                                            {
                                                "directive": "proxy_pass",
                                                "line": 7,
                                                "args": ["http://not.broken.example"],
                                            }
                                        ],
                                    },
                                ],
                            }
                        ],
                    }
                ],
            }
        ],
    }

    # test correct error is raised when broken proxy_pass is in lower block
    below_config = os.path.join(dirname, "broken-below.conf")
    below_payload = parser.parse(below_config)
    assert below_payload == {
        "status": "failed",
        "errors": [
            {
                "file": below_config,
                "error": 'directive "proxy_pass" is not terminated by ";" in %s:7'
                % below_config,
                "line": 7,
            }
        ],
        "config": [
            {
                "file": below_config,
                "status": "failed",
                "errors": [
                    {
                        "error": 'directive "proxy_pass" is not terminated by ";" in %s:7'
                        % below_config,
                        "line": 7,
                    }
                ],
                "parsed": [
                    {
                        "directive": "http",
                        "line": 1,
                        "args": [],
                        "block": [
                            {
                                "directive": "server",
                                "line": 2,
                                "args": [],
                                "block": [
                                    {
                                        "directive": "location",
                                        "line": 3,
                                        "args": ["/not-broken"],
                                        "block": [
                                            {
                                                "directive": "proxy_pass",
                                                "line": 4,
                                                "args": ["http://not.broken.example"],
                                            }
                                        ],
                                    },
                                    {
                                        "directive": "location",
                                        "line": 6,
                                        "args": ["/is-broken"],
                                        "block": [],
                                    },
                                ],
                            }
                        ],
                    }
                ],
            }
        ],
    }


def test_comments_between_args():
    dirname = os.path.join(here, "configs", "comments-between-args")
    config = os.path.join(dirname, "nginx.conf")
    payload = parser.parse(config, comments=True)
    assert payload == {
        "status": "ok",
        "errors": [],
        "config": [
            {
                "file": config,
                "status": "ok",
                "errors": [],
                "parsed": [
                    {
                        "directive": "http",
                        "line": 1,
                        "args": [],
                        "block": [
                            {
                                "directive": "#",
                                "line": 1,
                                "args": [],
                                "comment": "comment 1",
                            },
                            {
                                "directive": "log_format",
                                "line": 2,
                                "args": ["\\#arg\\ 1", "#arg 2"],
                            },
                            {
                                "directive": "#",
                                "line": 2,
                                "args": [],
                                "comment": "comment 2",
                            },
                            {
                                "directive": "#",
                                "line": 2,
                                "args": [],
                                "comment": "comment 3",
                            },
                            {
                                "directive": "#",
                                "line": 2,
                                "args": [],
                                "comment": "comment 4",
                            },
                            {
                                "directive": "#",
                                "line": 2,
                                "args": [],
                                "comment": "comment 5",
                            },
                        ],
                    }
                ],
            }
        ],
    }
