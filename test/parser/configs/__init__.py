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
