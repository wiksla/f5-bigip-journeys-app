import filecmp
import io
import logging
import os
import tarfile
import tempfile
from contextlib import redirect_stdout

import gnupg

from journeys.errors import JourneysError

log = logging.getLogger(__name__)


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
                raise JourneysError("Failed to decrypt archive")

    with tarfile.open(decrypted_archive_file) as tar:
        members = tar.getmembers()
        files_metadata = {}
        for member in members:
            tar.extract(member=member, path=output_dir, set_attrs=False)
            files_metadata[member.path] = member

    if archive_passphrase:
        os.remove(decrypted_archive_file)

    return output_dir, files_metadata


def tar_file(
    archive_file,
    input_dir,
    files_metadata,
    archive_passphrase=None,
    excluded_files=None,
):
    decrypted_archive_file = archive_file
    if archive_passphrase:
        decrypted_archive_file = archive_file + ".decrypted"

    # change directory to input directory
    current_dir = os.getcwd()
    os.chdir(input_dir)

    excluded_files = excluded_files or [".git", ".gitignore", ".shelf"]

    def reset_metadata(tarinfo):
        if tarinfo.path in excluded_files:
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
                raise JourneysError("Failed to encrypt archive")

        os.remove(decrypted_archive_file)

    return archive_file


def compare_archives(
    source_archive_fn: str,
    destination_archive_fn: str,
    source_passphrase=None,
    destination_passphrase=None,
) -> str:
    """Returns recursively compared contents of two archives as a string. """
    with tempfile.TemporaryDirectory() as tmp_dir:
        dirs = [f"{tmp_dir}/{source_archive_fn}", f"{tmp_dir}/{destination_archive_fn}"]
        for d in dirs:
            os.mkdir(d)

        files = [source_archive_fn, destination_archive_fn]
        passwds = [source_passphrase, destination_passphrase]
        for archive, passwd, dir_name in zip(files, passwds, dirs):
            untar_file(archive, dir_name, passwd)

        comparison = filecmp.dircmp(*dirs)
        report = get_comparison_report(comparison)

    return report


def get_comparison_report(comparison: filecmp.dircmp) -> str:
    """Returns stdout from report_full_closure execution as a string. """
    f = io.StringIO()
    with redirect_stdout(f):
        comparison.report_full_closure()

    return f.getvalue()
