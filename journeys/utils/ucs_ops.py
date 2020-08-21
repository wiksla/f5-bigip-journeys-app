import os
import shutil
import tarfile

import gnupg


def untar_file(archive_file, output_dir, archive_passphrase=None):
    decrypted_archive_file = archive_file
    if archive_passphrase:
        decrypted_archive_file = archive_file + ".decrypted"

        gpg = gnupg.GPG()
        with open(archive_file, "rb") as encrypted_file:
            crypt = gpg.decrypt_file(
                file=encrypted_file,
                passphrase=archive_passphrase,
                output=decrypted_archive_file,
            )

            if not crypt.ok:
                raise RuntimeError("Failed to decrypt archive")

    with tarfile.open(decrypted_archive_file) as tar:
        members = tar.getmembers()
        files_metadata = {}
        for member in members:
            tar.extract(member=member, path=output_dir, set_attrs=False)
            files_metadata[member.path] = member

    if archive_passphrase:
        os.remove(decrypted_archive_file)

    return output_dir, files_metadata


def tar_file(archive_file, input_dir, files_metadata, archive_passphrase=None):
    decrypted_archive_file = archive_file
    if archive_passphrase:
        decrypted_archive_file = archive_file + ".decrypted"

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

    with tarfile.open(os.path.join(current_dir, decrypted_archive_file), "w:gz") as tar:
        for f in os.listdir("."):
            tar.add(name=f, recursive=True, filter=reset_metadata)
    tar.close()

    # change directory to original one
    os.chdir(current_dir)

    if archive_passphrase:
        gpg = gnupg.GPG()

        cipher = "AES128"  # https://support.f5.com/csp/article/K5437

        with open(decrypted_archive_file, "rb") as decrypted_file:
            crypt = gpg.encrypt_file(
                file=decrypted_file,
                recipients=None,  # not used with symmetric encryption
                symmetric=cipher,
                passphrase=archive_passphrase,
                output=archive_file,
            )
            if not crypt.ok:
                raise RuntimeError("Failed to encrypt archive")

        os.remove(decrypted_archive_file)

    return archive_file


def delete_temp_dir(temp_dir):
    shutil.rmtree(temp_dir, ignore_errors=True)
