import pytest

from journeys.utils.image import parse_version_file
from journeys.utils.image import short_edition

VERSION_FILE_1 = """
Product: BIG-IP
Version: 12.1.1
Build: 0.0.184
Sequence: 12.1.1.0.0.184.0
BaseBuild: 0.0.184
Edition: Final
Date: Thu Aug 11 17:09:01 PDT 2016
Built: 160811170901
Changelist: 1874858
JobID: 705993
""".strip()

VERSION_INFO_1 = {
    "product": "BIG-IP",
    "built": "160811170901",
    "sequence": "12.1.1.0.0.184.0",
    "basebuild": "0.0.184",
    "changelist": "1874858",
    "jobid": "705993",
    "edition": "Final",
    "version": "12.1.1",
    "build": "0.0.184",
    "date": "Thu Aug 11 17:09:01 PDT 2016",
}

VERSION_FILE_1HF = """
Product: BIG-IP
Version: 12.1.1
Build: 1.0.196
Sequence: 12.1.1.1.0.196.0
BaseBuild: 0.0.184
Edition: Hotfix HF1
Date: Wed Sep  7 17:48:09 PDT 2016
Built: 160907174809
Changelist: 1899499
JobID: 722136
""".strip()

VERSION_INFO_1HF = {
    "product": "BIG-IP",
    "built": "160907174809",
    "sequence": "12.1.1.1.0.196.0",
    "basebuild": "0.0.184",
    "changelist": "1899499",
    "jobid": "722136",
    "edition": "Hotfix HF1",
    "version": "12.1.1",
    "build": "1.0.196",
    "date": "Wed Sep  7 17:48:09 PDT 2016",
}


@pytest.mark.parametrize(
    "version_file,expected_result",
    [(VERSION_FILE_1, VERSION_INFO_1), (VERSION_FILE_1HF, VERSION_INFO_1HF)],
)
def test_parse_version_file(version_file, expected_result):
    assert parse_version_file(version_file=version_file) == expected_result


@pytest.mark.parametrize(
    "edition, _short_edition",
    [
        (None, None),
        ("Final", "Final"),
        ("Hotfix HF1", "HF1"),
        ("Hotfix DUMMY", "HF"),
        ("Point Release 1", "PR1"),
        ("Point Release DUMMY", "Point Release DUMMY"),
        ("Engineering Hotfix HF1", "ENG HF1"),
        ("Engineering Hotfix DUMMY", "ENG"),
        ("POC Release 1", "POC1"),
        ("POC Release DUMMY", "POC"),
    ],
)
def test_short_edition_parsing(edition, _short_edition):
    assert short_edition(edition) == _short_edition
