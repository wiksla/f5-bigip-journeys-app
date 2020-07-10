import configparser
import os
from functools import partial

from journeys.config import Config


class UcsReader:
    """ Component used to get data from extracted ucs """

    def __init__(self, extracted_ucs_dir):
        self.ucs_path = partial(os.path.join, extracted_ucs_dir)
        self.ucs_platform_kwargs = self._get_ucs_platform_kwargs()

    def get_config(self):
        return Config.from_dir(self.ucs_path("config"))

    def get_ucs_platform(self):
        return self.ucs_platform_kwargs["platform"]

    def _get_ucs_platform_kwargs(self):
        """ keys: platform, family, host, systype """
        ucs_version_fn = self.ucs_path("config/.ucs_platform")

        with open(ucs_version_fn) as ucs_file:
            return dict(
                (line.split("=")[0].lower(), line.split("=")[1].strip())
                for line in ucs_file
            )

    def get_version_file(self):
        ucs_version_fn = self.ucs_path("config/ucs_version")

        with open(ucs_version_fn) as version_fd:
            return version_fd.read()

    def get_bigdb_variable(self, key, option):
        big_db_dat_fn = self.ucs_path("config/BigDB.dat")

        config = configparser.ConfigParser()
        config.read(big_db_dat_fn)

        try:
            return config[key].get(option=option, fallback="Option name is wrong")
        except KeyError:
            return None
