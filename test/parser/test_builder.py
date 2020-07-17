import pytest

from journeys.parser.builder import build
from journeys.parser.parser import parse

from .configs import list_config_files
from .configs import raw_config


@pytest.mark.parametrize("config_file", list_config_files())
def test_builder(config_file):
    raw_cnf = raw_config(config_file=config_file)

    parsed = parse(raw_cnf)
    built = build(payload=parsed["config"][0]["parsed"])

    assert raw_cnf == built
