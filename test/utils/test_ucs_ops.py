import filecmp
import os
import tarfile
import tempfile
from pathlib import Path

from journeys.utils.ucs_ops import compare_archives
from journeys.utils.ucs_ops import get_comparison_report


def test_get_comparison_report():
    with tempfile.TemporaryDirectory() as dir_a, tempfile.TemporaryDirectory() as dir_b:
        (Path(dir_a) / "config").mkdir()
        compare = filecmp.dircmp(dir_a, dir_b)
        report = get_comparison_report(compare)
        assert type(report) == str
        assert report.endswith("['config']\n")


def test_compare_archives():
    with tempfile.TemporaryDirectory() as parent_test_dir:
        os.chdir(parent_test_dir)
        Path("dir_a").mkdir()
        Path("dir_b").mkdir()
        with tarfile.open("archive_a", "w") as archive_a:
            archive_a.add("dir_a")

        Path("dir_a/config").mkdir()

        with tarfile.open("archive_b", "w") as archive_b:
            archive_b.add("dir_a")
            archive_b.add("dir_b")

        report = compare_archives("archive_a", "archive_b")
        assert type(report) == str
        assert report.endswith("['config']\n")
