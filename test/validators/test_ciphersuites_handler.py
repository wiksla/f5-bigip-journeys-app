from journeys.validators.ciphersuites_handler import _get_raw_suites
from journeys.validators.ciphersuites_handler import _parse_header
from journeys.validators.ciphersuites_handler import _parse_suite_row
from journeys.validators.ciphersuites_handler import _remove_row_numbering
from journeys.validators.ciphersuites_handler import get_ciphersuites


def test_get_raw_suites(bigip_mock):
    assert _get_raw_suites(bigip_mock).startswith("       ID  SUITE ")


def test_parse_header():
    line = (
        "ID  SUITE                            BITS PROT    CIPHER              MAC "
        "    KEYX\n "
    )
    header = _parse_header(line)
    assert header == ("ID", "SUITE", "BITS", "PROT", "CIPHER", "MAC", "KEYX")


def test_remove_numbering():
    line = " 49171  ECDHE-RSA-AES128-CBC-SHA         128  TLS1   AES"
    line1 = " 1: 49171  ECDHE-RSA-AES128-CBC-SHA         128  TLS1   AES"
    line66 = " 66: 49171  ECDHE-RSA-AES128-CBC-SHA         128  TLS1   AES"
    line76 = " 76: 49171  ECDHE-RSA-AES128-CBC-SHA         128  TLS1   AES"
    line200 = " 200: 49171  ECDHE-RSA-AES128-CBC-SHA         128  TLS1   AES"
    assert _remove_row_numbering(line1) == line
    assert _remove_row_numbering(line66) == line
    assert _remove_row_numbering(line76) == line
    assert _remove_row_numbering(line200) == line


def test_parse_suites_row():
    row = (
        "5:    57  DHE-RSA-AES256-SHA               256  TLS1.2  Native  AES       "
        "SHA     EDH/RSA "
    )
    result = _parse_suite_row(row)
    assert result == (
        "57",
        "DHE-RSA-AES256-SHA",
        "256",
        "TLS1.2",
        "Native",
        "AES",
        "SHA",
        "EDH/RSA",
    )


def test_get_ciphersuites(bigip_mock):
    parsed_suites = get_ciphersuites(bigip_mock)
    assert type(parsed_suites) == list
    assert type(parsed_suites[0]) == dict
    assert len(parsed_suites[0].keys()) == 7
    assert parsed_suites[0]["SUITE"] == "ECDHE-RSA-AES128-GCM-SHA256"
