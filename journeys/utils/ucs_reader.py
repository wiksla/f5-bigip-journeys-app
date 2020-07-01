import os


class UcsReader:
    """ Component used to get data from extracted ucs """

    def __init__(self, extracted_ucs_dir):
        self.extracted_ucs_dir = extracted_ucs_dir
        self.ucs_platform_kwargs = self._get_ucs_platform_kwargs()

    def get_ucs_platform(self):
        return self.ucs_platform_kwargs["platform"]

    def _get_ucs_platform_kwargs(self):
        """ keys: platform, family, host, systype """
        ucs_version_fn = os.path.join(self.extracted_ucs_dir, "config/.ucs_platform")

        with open(ucs_version_fn) as ucs_file:
            return dict(
                (line.split("=")[0].lower(), line.split("=")[1].strip())
                for line in ucs_file
            )

    def get_version_file(self):
        ucs_version_fn = os.path.join(self.extracted_ucs_dir, "config/ucs_version")
        with open(ucs_version_fn) as version_fd:
            return version_fd.read()
