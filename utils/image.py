
import re
from os import path

import isoparser


class SetupError(Exception):
    def __init__(self, message):
        self.message = message


def get_image_from_ucs_reader(ucs_reader):
    return Version(**parse_version_file(ucs_reader.get_version_file()))


class Version:
    def __init__(self, **version_info):
        self.product = version_info.pop('product', None)
        self.version = version_info.pop('version', None)
        self.build = version_info.pop('build', None)
        self.sequence = version_info.pop('sequence', None)
        self.basebuild = version_info.pop('basebuild', None)
        self.edition = version_info.pop('edition', None)
        self.short_edition = short_edition(self.edition)
        self.branch = version_info.pop("project") if version_info.get("project") else None

        self.unclassified = version_info
        self.friendly_name = self.__repr__()

    def __eq__(self, other):
        return self.__dict__ == other.__dict__

    def __ne__(self, other):
        return self.__dict__ != other.__dict__

    def __hash__(self):
        return hash(''.join(str(x) for x in self.__dict__.values()))

    def __repr__(self):
        formatted = f"{self.version}-{self.build}" if self.version != "Rollback" else self.version
        if self.short_edition and self.short_edition != "Final" and "PR" not in self.short_edition:
            formatted += f" {self.short_edition}"
        if self.branch:
            formatted += f" ({self.branch})"
        return formatted


def get_image_version_file(image_fn):
    if not path.isfile(image_fn):
        raise SetupError('File does not exist: {}'.format(image_fn))

    root = isoparser.parse(image_fn).record()
    for record in root.children:
        if b'BIGIP' in record.name:
            for record in record.children:
                if b'VERSION' in record.name:
                    return record.content.decode("utf-8")
        elif b'VERSION' in record.name:
            return record.content.decode("utf-8")


def get_image_version(image_fn):
    return Version(**parse_version_file(
        get_image_version_file(image_fn=image_fn)))


def parse_version_file(version_file):
    version_info = {}
    for line in version_file.splitlines():
        split = line.split(':', 1)
        version_info[split[0].lower().strip()] = split[1].strip()
    return version_info


RE_HF = re.compile(r'^Hotfix (HF\d+)$')
RE_ENG_HF = re.compile(r'^Engineering Hotfix (HF\d+)$')
RE_PR = re.compile(r'^Point Release (\d+)*$')
RE_POC = re.compile(r'^POC Release (\d+)$')


def short_edition(edition):
    if edition is None:
        return None
    elif edition in ('Final', ):
        return edition
    elif edition.startswith('Hotfix '):
        m = RE_HF.match(edition)
        if m:
            return m.group(1)
        return 'HF'
    elif edition.startswith('Point Release'):
        m = RE_PR.match(edition)
        if m:
            return 'PR{}'.format(m.group(1))
        return edition
    elif edition.startswith('Engineering Hotfix'):
        m = RE_ENG_HF.match(edition)
        if m:
            return 'ENG {}'.format(m.group(1))
        return 'ENG'
    elif edition.startswith('POC Release'):
        m = RE_POC.match(edition)
        if m:
            return 'POC{}'.format(m.group(1))
        return 'POC'
    else:
        return edition
