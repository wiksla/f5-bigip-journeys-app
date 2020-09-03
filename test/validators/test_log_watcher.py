# from test.validators.conftest import TEST_OUTPUT_ROOT

from test.validators.conftest import stat_file_output

# from mock import MagicMock
# from mock import call
from mock import patch

from journeys.validators.log_watcher import LogWatcher

# from test.validators.conftest import get_file_output

# :TODO adjust log_watcher_unit_tests !!!


@patch(
    "journeys.validators.log_watcher.stat_file", return_value=stat_file_output,
)
def test_log_watcher_stats_logs_on_start(bigip_mock):
    stat_file_output.st_size = 0
    log_watcher = LogWatcher(bigip_mock, {"testfile": "err"})
    log_watcher.start()
    assert log_watcher._pointers["testfile"] == 0


# @patch(
#     "journeys.validators.log_watcher.stat_file",
#     return_value=stat_file_output,
# )
# @patch("journeys.validators.log_watcher.Path.open", MagicMock())
# def test_log_watcher_stops(bigip_mock):
#     """test get_file is executed for each defined path"""
#     log_watcher = LogWatcher(device=bigip_mock, logs={"testfile": "err", "tst2": "debug"})
#     output = TEST_OUTPUT_ROOT / "local_temp_fs"
#     log_watcher._LogWatcher__tmppath = output
#     log_watcher._LogWatcher__tmpdir = MagicMock()
#     log_watcher.start()
#     log_watcher.stop()
#     calls = [
#         call("testfile", f"{output}/testfile"),
#         call("tst2", f"{output}/tst2"),
#     ]
#     bigip_mock.get_file.assert_has_calls(calls)
#     log_watcher._LogWatcher__tmpdir.cleanup.assert_called_once()
