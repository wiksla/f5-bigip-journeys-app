import os
import shutil
import tarfile
from subprocess import call


def untar_file(archive_file, output_dir, sub_dir: str = None):
    with tarfile.open(archive_file) as tar:
        path = os.path.join(output_dir, sub_dir) if sub_dir else output_dir
        for member in tar.getmembers():
            tar.extract(member=member, path=path, set_attrs=False)
    return output_dir


def tar_file(archive_file, input_dir):
    ucs_path = os.path.join(input_dir, archive_file)
    # tar is deliberately called from shell in this specific way, since it's
    # the only way BIG-IP accepts the ucs. DO NOT touch this row unless you've
    # tested it end to end.
    cmd = "cd {} ; tar -czf {} *".format(input_dir, archive_file)
    call(cmd, shell=True)
    return ucs_path


def delete_temp_dir(temp_dir):
    shutil.rmtree(temp_dir, ignore_errors=True)
