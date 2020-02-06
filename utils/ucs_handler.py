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
#
#
# def _get_config_filenames(filename):
#     """ List all files in /config. """
#     try:
#         config_filenames = subprocess.check_output(['tar', '-tf', filename, 'config'], stderr=subprocess.STDOUT)
#     except subprocess.CalledProcessError:
#         print("File {} does not exist.".format(filename))
#         return None
#     else:
#         return config_filenames.split()


# for x in _get_config_filenames(filename='/home/mj/Desktop/resource/ucs_vcmp_host.ucsA'):
#     print(x)
