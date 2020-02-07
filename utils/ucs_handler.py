import os
import shutil
import subprocess

from tempfile import mkdtemp


HOST_FILE = "config/bigip.conf"


def obtain_data_from_host(ucs_fn, obtain):
    temp_dir = mkdtemp()
    try:
        extract_host_file(ucs_fn=ucs_fn, extract_dir_destination=temp_dir)
        return obtain(os.path.join(temp_dir, HOST_FILE))
    finally:
        shutil.rmtree(temp_dir)


def extract_host_file(ucs_fn, extract_dir_destination):
    """ Extract specified config files to location: extract_dir_destination . """
    cmd = ["tar", "-xf", ucs_fn, "-C", extract_dir_destination, HOST_FILE]
    subprocess.call(cmd)


# def extract_all_files(filename, extract_dir_destination):
#     cmd = ['tar', '-xf', filename,  extract_dir_destination]
#     subprocess.call(cmd)


def file_is_proper_ucs(ucs_fn):
    try:
        config_filenames = subprocess.check_output(['tar', '-tf', ucs_fn, 'config'], stderr=subprocess.STDOUT)
    except subprocess.CalledProcessError:
        print("File {} does not exist !".format(ucs_fn))
        pass
    else:
        return HOST_FILE.encode("utf-8") in config_filenames.split()
