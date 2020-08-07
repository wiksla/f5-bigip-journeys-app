import os
import shutil
import tarfile


def untar_file(archive_file, output_dir, sub_dir: str = None):
    with tarfile.open(archive_file) as tar:
        path = os.path.join(output_dir, sub_dir) if sub_dir else output_dir
        members = tar.getmembers()
        files_metadata = {}
        for member in members:
            tar.extract(member=member, path=path, set_attrs=False)
            files_metadata[member.path] = member
    return output_dir, files_metadata


def tar_file(archive_file, input_dir, files_metadata):

    # change directory to input directory
    current_dir = os.getcwd()
    os.chdir(input_dir)

    def reset_metadata(tarinfo):
        if tarinfo.path in [".git", ".gitignore", ".shelf"]:
            return None

        try:
            orig_tarinfo = files_metadata[tarinfo.path]
            tarinfo.uid = orig_tarinfo.uid
            tarinfo.gid = orig_tarinfo.gid
            tarinfo.uname = orig_tarinfo.uname
            tarinfo.gname = orig_tarinfo.gname
            tarinfo.mode = orig_tarinfo.mode
        except KeyError:
            pass

        return tarinfo

    with tarfile.open(archive_file, "w:gz") as tar:
        for f in os.listdir("."):
            tar.add(name=f, recursive=True, filter=reset_metadata)
    tar.close()

    # change directory to original one
    os.chdir(current_dir)

    return archive_file


def delete_temp_dir(temp_dir):
    shutil.rmtree(temp_dir, ignore_errors=True)
