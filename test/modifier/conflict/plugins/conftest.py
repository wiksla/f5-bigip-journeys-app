import tarfile
from contextlib import closing
from io import BytesIO
from tempfile import mkdtemp
from time import time

import pytest

from journeys.controller import MigrationController

DEFAULT_UCS_FILE_NAME = "test_config.ucs"
DEFAULF_BRANCHES = set(["initial", "master"])
DEFAULT_CONFIG_DB_NAME = "config/BigDB.dat"
DEFAULT_CONFIG_FILE_NAME = "config/bigip_base.conf"


@pytest.fixture
def test_solution(ucs, controller):
    def _test_solution(conflict_name, solution_name, conf_file="", conf_dat_file=""):
        usc_file = ucs(
            conf_file=(conf_file, DEFAULT_CONFIG_FILE_NAME),
            dat_file=(conf_dat_file, DEFAULT_CONFIG_DB_NAME),
            output_file=DEFAULT_UCS_FILE_NAME,
        )

        obj_controller = controller(input_ucs=usc_file, clear=True)
        conflicts = obj_controller.process()

        assert obj_controller.repo
        assert conflicts
        assert conflict_name in conflicts

        obj_controller.resolve(conflict_name)
        repo_heads = set(obj_controller.repo.heads) - DEFAULF_BRANCHES

        assert len(repo_heads) > 0

        obj_controller.repo.git.checkout(".")
        obj_controller.repo.git.merge(solution_name)

        del obj_controller
        obj_controller = controller(input_ucs=usc_file)
        _ = obj_controller.process()

        return obj_controller

    return _test_solution


@pytest.fixture
def ucs():
    def _ucs(conf_file, dat_file, output_file):
        temp_dir = mkdtemp()
        temp_file_path = temp_dir + output_file
        with tarfile.open(temp_file_path, "w") as tf:
            for file in {conf_file, dat_file}:
                with closing(BytesIO(file[0].encode())) as fobj:
                    tarinfo = tarfile.TarInfo(file[1])
                    tarinfo.size = len(fobj.getvalue())
                    tarinfo.mtime = time()
                    tf.addfile(tarinfo, fileobj=fobj)

        return temp_file_path

    return _ucs


@pytest.fixture
def controller():
    def _controller(input_ucs, clear=False):
        controller = MigrationController(allow_empty=True, clear=clear)
        if clear:
            controller.initialize(input_ucs=input_ucs, ucs_passphrase="")

        return controller

    return _controller
