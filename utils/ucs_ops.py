import os
import shutil
import tarfile
from subprocess import call

from tempfile import mkdtemp


def untar_file(archive_file, dir):
    output_dir = mkdtemp(prefix='migration_ucs_', dir=dir)
    with tarfile.open(archive_file) as tar:
        tar.extractall(path=output_dir)
    return output_dir


def tar_file(archive_file, input_dir):
    ucs_path = os.path.join(input_dir, archive_file)
    # tar is deliberately called from shell in this specific way, since it's
    # the only way BIG-IP accepts the ucs. DO NOT touch this row unless you've
    # tested it end to end.
    cmd = 'cd {} ; tar -czf {} *'.format(input_dir, archive_file)
    call(cmd, shell=True)
    return ucs_path


def delete_temp_dir(temp_dir):
    shutil.rmtree(temp_dir, ignore_errors=True)
