from __future__ import annotations

import configparser
import logging
import re
from copy import deepcopy
from dataclasses import dataclass
from dataclasses import field as dataclass_field
from pathlib import Path
from typing import Iterable
from typing import Optional
from typing import Union

from journeys.errors import BigDbError
from journeys.errors import InputFileNotExistError
from journeys.parser import build_files
from journeys.parser import parse_file
from journeys.parser.builder import build
from journeys.parser.const import NONAME
from journeys.parser.parser import parse_dir

log = logging.getLogger(__name__)


class Config:
    @classmethod
    def from_conf(cls, filename: str) -> Config:
        with open(filename, "r") as f:
            config = parse_file(f, filename)
        return cls(config)

    @classmethod
    def from_string(cls, string: str, out_filename: str = "bigip.conf") -> Config:
        config = parse_file(string, out_filename)
        return cls(config)

    @classmethod
    def from_dir(cls, dirname: str) -> Config:
        config = parse_dir(dirname)
        bigdb = BigDB(dirname=dirname)
        return cls(config, bigdb)

    def __init__(self, config: dict, bigdb=None):
        self.data = config
        self.bigdb = bigdb
        self.combined_fields = self._combine_fields()
        self.field_collection = FastFieldCollection(
            self.combined_fields, self, TopLevelField
        )

    def _combine_fields(self) -> list:
        out = []
        for conf in self.data["config"]:
            for field in conf["parsed"]:
                field["file"] = conf["file"]
                out.append(field)
        return out

    def _rebuild_data(self):
        """Read all items from combined_fields
        and fill in their respective field lists in original data.
        """
        file_index = {}
        for idx, conf in enumerate(self.data["config"]):
            file_index[conf["file"]] = idx
            conf["parsed"] = []

        for item in self.combined_fields:
            try:
                index = file_index[item["file"]]
                self.data["config"][index]["parsed"].append(item)
            except KeyError as e:
                id_ = " ".join(item["args"])
                if "file" in str(e):
                    log.warn(
                        f"Build: Key 'file' not found for root field {id_}. Skipping."
                    )
                else:
                    log.debug(
                        f"Build: File {item['file']} for {id_} does not exist in original config. Adding it."
                    )
                    d = {
                        "file": item["file"],
                        "status": "ok",
                        "errors": [],
                        "parsed": [item],
                    }
                    self.data["config"].append(d)
                    file_index[item["file"]] = len(self.data["config"]) - 1

    @property
    def fields(self) -> FastFieldCollection:
        """Return an instance of all top level fields in the config."""
        return self.field_collection

    def build(self, dirname: Optional[str] = None, files: Iterable[str] = None):
        """Build the conf file using the stored data.

        Filenames will be the same as in original input files.
        """
        if self.bigdb:
            self.bigdb.save()
        self._rebuild_data()
        build_files(self.data, dirname=dirname, files=files)


class Field:
    __slots__ = ("data", "parent")

    def __init__(self, block: dict, parent: FieldCollection):
        self.data = block
        self.parent = parent

    @property
    def key(self) -> str:
        """Get the key - the first field argument."""
        try:
            return self.data["args"][0]
        except IndexError:
            return None

    @key.setter
    def key(self, key: Union[str, None]):
        """Set the key - the first field argument."""
        old_args = self.args
        if key is not None:
            self.data["args"][0] = key
        else:
            self.data["args"] = []
        self.parent.update(self, old_args)

    @property
    def args(self) -> tuple:
        """Return a tuple of all field arguments - key + values."""
        return tuple(self.data["args"])

    @args.setter
    def args(self, args: Iterable[str]):
        """Set all arguments - key + values at once."""
        old_args = self.args
        self.data["args"] = list(args)
        self.parent.update(self, old_args)

    @property
    def fields(self) -> Optional[FieldCollection]:
        if "block" in self.data:
            return FieldCollection(self.data["block"], self)
        else:
            return None

    @property
    def value(self) -> str:
        """Return any arguments following the field key."""
        # are there any non-top fields that have both? or more than one arg?
        return " ".join(self.data["args"][1:])

    @value.setter
    def value(self, value: Union[str, Iterable[str], None]):
        """Set the field value.
        For convenience you can provide a string to set a single word value.
        Provide a tuple for multi-word ones.
        """
        old_args = self.args
        if isinstance(value, str):
            self.data["args"][1:] = [value]
        elif value is None:
            self.data["args"][1:] = []
        else:
            self.data["args"][1:] = list(value)
        self.parent.update(self, old_args)

    @property
    def id(self) -> str:
        """Return a block identifier - all arguments without any nested blocks.

        Note that the id may not necessarily be unique outside of depth=0.
        """
        return " ".join(self.args)

    def delete(self):
        """Remove self from parent collection."""
        self.parent.remove(self)

    def create_block(self):
        """If not existent yet, create an empty block that can accept new fields.

        After this operation, c.fields will always return a FieldCollection
        instead of None.
        Return self to allow further chaining."""
        if "block" not in self.data:
            self.data["block"] = []

    def delete_block(self):
        """Remove a block with any contents from the field, leaving only args."""
        self.data.pop("block", "")

    def insert_before(self, args: Iterable[str] = None, block: bool = False):
        """Convenience function to insert a field before
        the current one in the parent collection.

        Uses the same 'args' and 'block' arguments as FieldCollection.add.
        """
        index = self.parent.index(self)
        kwargs = {"args": args, "block": block, "index": index}
        if "file" in self.data:
            kwargs["file"] = self.data["file"]

        return self.parent.add(**kwargs)

    def insert_after(self, args: Iterable[str] = None, block: bool = False):
        """Convenience function to insert a field after
        the current one in the parent collection.

        Uses the same 'args' and 'block' arguments as FieldCollection.add.
        """
        index = self.parent.index(self)
        kwargs = {"args": args, "block": block, "index": index + 1}
        if "file" in self.data:
            kwargs["file"] = self.data["file"]

        return self.parent.add(**kwargs)

    def convert_to_comments(self):
        """Converts self into a set of comment fields,
        inserts them in the parent collection, them removes self from it.
        """
        built = build([self.data])
        for line in built.splitlines():
            field = self.insert_before(["#"])
            field.data["comment"] = line
            if "file" in self.data:
                field.data["file"] = self.data["file"]

        self.delete()

    def __eq__(self, other: Field):
        return other.data is self.data

    def __repr__(self):
        suffix = " {..}" if self.fields else ""
        return f"<{self.__class__.__name__} id {id(self)}: {self.id}{suffix}>"

    def __str__(self):
        return build([self.data])


class TopLevelField(Field):
    @property
    def module(self) -> str:
        return self.data["args"][0]

    @property
    def type(self) -> Optional[str]:
        if self.args in NONAME:
            return self.args[1:]
        else:
            return self.args[1:-1]

    @property
    def name(self) -> Optional[str]:
        if self.args in NONAME:
            return None
        else:
            return self.args[-1]

    @property
    def key(self) -> str:
        """Get a key - all arguments as a top level field."""
        # For top level items, the whole directive + args consitute a key
        return self.id

    @property
    def file(self) -> str:
        """Return the file to which this field is assigned to."""
        return self.data["file"]

    @file.setter
    def file(self, value):
        self.data["file"] = value


class FieldCollection:
    def __init__(
        self, block: list, parent: Union[Field, Config], field_class: type = Field
    ):
        self.data = block
        self.parent = parent
        self.field_cls = field_class

    def __len__(self):
        return len(self.data)

    def get(self, item: Union[int, str, tuple]) -> Field:
        """Return the first element matching the criteria.

        Three options for searching:
        int - gets the field under the given index
        string - searches for the field with the given key
        tuple - matches the starting arg list
        For more complex cases check the _re counterpart.
        Examples:
        fields.get(0)
        fields.get('ltm node /Common/node')
        fields.get(('ltm', 'node', '/Common/node'))
        fields.get(('ltm',)) - returns the first item from the ltm module.
        """
        if isinstance(item, int):
            return self.field_cls(self.data[item], self)
        if isinstance(item, str):
            for field in self.all():
                if field.key == item:
                    return field
        else:
            try:
                return next(self.get_all(item))
            except StopIteration:
                pass
        raise KeyError(f"Requested field {item} not found.")

    def get_all(self, item: tuple) -> Iterable[Field]:
        """Return a generator of all elements matching the criteria.

        Examples:
        fields.get(('ltm', 'node', '/Common/node'))
        fields.get(('ltm',))
        """
        for field in self.all():
            if item == field.args[: len(item)]:
                yield field

    def get_re(self, regex: str) -> Field:
        """Return the first item matching the pattern."""
        try:
            return next(self.get_all_re(regex))
        except StopIteration:
            pass
        raise KeyError(f"Pattern {regex} not found.")

    def get_all_re(self, regex: str) -> Iterable[Field]:
        """Return a generator of all elements matching the pattern."""
        r = re.compile(regex)
        for field in self.all():
            if re.match(r, field.id):
                yield field

    def all(self) -> Iterable[Field]:
        """Return a generator of all non-comment elements."""
        for item in self.data:
            if item["args"] and not item["args"][0].startswith("#"):
                yield self.field_cls(item, self)

    def add_data(self, data: dict, index: Optional[int] = None, copy: bool = True):
        """Inserts a field in a dict format into the collection.
        This can be extracted from an existing field via the 'data' attribute.

        index - index in which to insert the new field. End by default
        copy - whether to create a deepcopy of the dict before inserting it

        Returns a Field instance pointing to the inserted data.
        """

        to_insert = deepcopy(data) if copy else data

        if index is None:
            self.data.append(to_insert)
        else:
            self.data.insert(index, to_insert)

        return self.field_cls(to_insert, self)

    def add(
        self,
        args: Iterable[str] = None,
        block: bool = False,
        index: Optional[int] = None,
        file: Optional[str] = None,
    ) -> Field:
        """Add a new field to this collection.

          args - the list of arguments defining the field. If none, the field
        will be treated as an unnamed one.
          block - whether to initialize an empty { } block inside the field
          index - index in which to insert the new field. End by default
          file - assign a file value to the newly created field. Necessary if we're creating
        top level fields

        Examples:
        c.fields.add(('ltm', 'pool', '/Common/pool'), True)
        pool.fields.add(('monitor', '/Common/monitor'))
        """
        # TODO: type and name for top level fields?
        args = args or []
        d = {"args": list(args)}
        if block:
            d["block"] = {}

        if issubclass(self.field_cls, TopLevelField) and file is None:
            raise ValueError(
                "File argument needs to be defined when adding a top level field."
            )

        if file is not None:
            d["file"] = file

        field = self.add_data(d, index, False)
        return field

    def remove(self, field: Field):
        """Remove the given field from the collection."""
        self.data.remove(field.data)

    def update(self, field: Field, old_args: tuple):
        """Perform any actions after a field update."""
        pass

    def index(self, field: Field):
        """Get the index of the element 'field' in the current collection."""
        return self.data.index(field.data)

    def __getitem__(self, key: Union[str, int, tuple]) -> Field:
        """Return the first field matching the key.

        Check get() method docs for details."""
        return self.get(key)

    def __contains__(self, item: Union[str, tuple]):
        try:
            self.get(item)
        except KeyError:
            return False
        return True

    def __repr__(self):
        fields_str = ""
        idx = -1
        for idx, field in enumerate(self.all()):
            if idx < 2:
                fields_str += str(field) + " "
        if idx > 2:
            fields_str += "[...] "
        if idx > 1:
            fields_str += str(field)
        return f"<{self.__class__.__name__} id {id(self)}: {fields_str}>"


class FastFieldCollection(FieldCollection):
    """A FieldCollection, but with a lookup tree.
    Will only work with the assumption that keys will be unique.
    """

    @dataclass
    class _Node:
        value: Field = None
        tree: dict = dataclass_field(default_factory=dict)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._arg_tree = self._Node()
        self._id_map = dict()

        # initialize lookup dicts
        # id_map - for string-based key searches
        # arg_tree - for tuple-based argument searches
        for field in self.all():
            self._id_map[field.key] = field
            self._tree_insert(field)

    def _tree_insert(self, field: Field):
        """Add a field on branches corresponding to field's args."""
        node = self._arg_tree
        for arg in field.args:
            node = node.tree.setdefault(arg, self._Node())
        node.value = field

    def _tree_delete(self, args: tuple):
        """Remove value from requested arg branch path and any stale branches."""
        nodes = [("", self._arg_tree)]
        # prepare the edge+node path
        for arg in args:
            nodes.append((arg, nodes[-1][1].tree[arg]))
        # remove the leaf
        nodes[-1][1].value = None
        # clean up empty branches:
        # starting from the removed leaf, check if we have any empty nodes
        #  (i.e. node with no values or children)
        # if so, remove the node and repeat with parent
        # until root, or until a non-empty node is found.
        for it in range(len(nodes) - 1, 0, -1):
            child = nodes[it][1]
            parent = nodes[it - 1][1]
            key = nodes[it][0]
            if not child.value and not child.tree:
                parent.tree.pop(key)
            else:
                break

    def get(self, item: Union[str, tuple, int], lookup=True) -> Field:
        """Return the first found element matching the criteria.
        Warning: if using lookup, this might not be the
          topmost field from the config matching the query.

        For examples check the parent method docstring.
        lookup - if true, will use the new structures for a faster search.
        """
        try:
            if isinstance(item, tuple):
                return next(self.get_all(item, lookup))
            if isinstance(item, str) and lookup:
                return self._id_map[item]
        except (StopIteration, KeyError):
            raise KeyError(f"Requested key {item} not found.")
        return super().get(item)

    def get_all(self, item: tuple, lookup=True) -> Iterable[Field]:
        """Return a generator of all elements matching the criteria.

        For examples check the parent method docstring.
        lookup - if true, will use the new structures for a faster search.
        """
        if lookup:
            start_node = self._arg_tree
            for arg in item:
                try:
                    start_node = start_node.tree[arg]
                except KeyError:
                    return
            yield from self._get_all(start_node)
        else:
            yield from super().get_all(item)

    def _get_all(self, node: _Node) -> Iterable[Field]:
        """Search the tree starting at node recursively."""
        if node.value is not None:
            yield node.value
        for child in node.tree.values():
            yield from self._get_all(child)

    def add_data(self, *args, **kwargs) -> Field:
        """Add a new field to this collection.

        Check the parent method for usage details.
        """
        field = super().add_data(*args, **kwargs)
        self._tree_insert(field)
        self._id_map[field.id] = field
        return field

    def remove(self, field: Field):
        """Remove the field from the current collection."""
        self._tree_delete(field.args)
        self._id_map.pop(field.id)
        super().remove(field)

    def update(self, field: Field, old_args: tuple):
        """Update internal lookup maps with the changed values."""
        self._tree_delete(old_args)
        self._tree_insert(field)
        self._id_map.pop(
            " ".join(old_args)
        )  # Note: works correctly only for toplevelfield as of now
        self._id_map[field.key] = field
        super().update(field, old_args)


class BigDB:
    FILENAME = "BigDB.dat"

    def __init__(self, dirname: str):
        self.path = Path(dirname).joinpath(BigDB.FILENAME)
        self.config = configparser.ConfigParser()
        self.load()

    def load(self):
        try:
            self.config.read(self.path)
        except (
            configparser.DuplicateSectionError,
            configparser.DuplicateOptionError,
        ) as e:
            raise BigDbError(e.message)

    def save(self):
        try:
            with open(self.path, "w") as cnf:
                self.config.write(cnf, space_around_delimiters=False)
        except FileNotFoundError:
            raise InputFileNotExistError(self.path)

    def set(self, section: str, option: str, value: str):
        self.config.set(section=section, option=option, value=value)

    def get(self, section: str, option: str):
        return self.config.get(section=section, option=option)
