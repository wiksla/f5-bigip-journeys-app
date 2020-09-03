from unittest.mock import MagicMock
from unittest.mock import patch

import pytest

from journeys.validators.core_watcher import list_cores
from journeys.validators.exceptions import JourneysError


@patch(
    "journeys.validators.core_watcher.list_dir",
    MagicMock(return_value=["dummy_file", "testcore.core.gz"]),
)
def test_list_cores_returns_core_files(bigip_mock):
    assert list_cores(bigip_mock) == ["testcore.core.gz"]


@patch(
    "journeys.validators.core_watcher.list_dir",
    MagicMock(return_value=["dummy_file", "testcore.core.gz"]),
)
def test_list_cores_raises_exception(bigip_mock):
    with pytest.raises(JourneysError):
        list_cores(bigip_mock, raise_exception=True)
