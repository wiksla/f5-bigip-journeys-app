import glob
import json
import os

from journeys.parser import lex
from journeys.parser.parser import parse

CONFIG_DIR = os.path.dirname(__file__)


def parse_config(config_file):
    cnf = os.path.join(CONFIG_DIR, config_file)
    with open(cnf) as cnf_fn:
        return parse(cnf_fn)


def lex_config(config_file):
    cnf = os.path.join(CONFIG_DIR, config_file)
    with open(cnf) as cnf_fn:
        return lex(cnf_fn, line_numbers=True)


def build_config(config_json_file):
    cnf = os.path.join(CONFIG_DIR, config_json_file)
    with open(cnf) as f_:
        return json.load(f_)


def raw_config(config_file):
    with open(config_file) as cnf_file:
        return cnf_file.read()


def list_config_files(ignore=("not_balanced", "with_comments")):
    config_files = glob.glob(os.path.join(CONFIG_DIR, "*/*.conf"))
    return [
        config_file
        for config_file in config_files
        if not any(pattern in config_file for pattern in ignore)
    ]
