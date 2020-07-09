from __future__ import annotations

import re
from typing import Iterable
from typing import Optional
from typing import Union

from journeys.parser import build_files
from journeys.parser import parse_file


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

    def __init__(self, config: dict):
        self.data = config

    @property
    def fields(self) -> FieldCollection:
        """Return an instance of all top level fields in the config."""
        return FieldCollection(self.data["config"][0]["parsed"], self, TopLevelField)

    def build(self, dirname: Optional[str] = None):
        """Build the conf file using the stored data.

        Filenames will be the same as in original input files.
        """
        build_files(self.data, dirname=dirname)


class Field:
    __slots__ = ("data", "parent")

    def __init__(self, block: dict, parent: FieldCollection):
        self.data = block
        self.parent = parent

    @property
    def key(self) -> str:
        """Get the key - the first field argument."""
        if self.data["directive"] == "_unnamed":
            return None
        else:
            return self.data["directive"]

    @key.setter
    def key(self, key: Union[str, None]):
        """Set the key - the first field argument."""
        if key is not None:
            self.data["directive"] = key
        else:
            self.data["directive"] = "_unnamed"

    @property
    def args(self) -> tuple:
        """Return a tuple of all field arguments - key + values."""
        return (self.data["directive"], *self.data["args"])

    @args.setter
    def args(self, args: Iterable[str]):
        """Set all arguments - key + values at once."""
        if not args:
            self.data["directive"] = "_unnamed"
            self.data["args"] = []
        else:
            self.data["directive"] = args[0]
            self.data["args"] = list(args[1:])

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
        return " ".join(self.data["args"])

    @value.setter
    def value(self, value: Union[str, Iterable[str], None]):
        """Set the field value.
        For convenience you can provide a string to set a single word value.
        Provide a tuple for multi-word ones.
        """
        if isinstance(value, str):
            self.data["args"] = [value]
        elif value is None:
            self.data["args"] = []
        else:
            self.data["args"] = list(value)

    def delete(self):
        """Remove self from parent collection."""
        self.parent.remove(self)

    @property
    def id(self) -> str:
        """Return a block identifier - all arguments without any nested blocks.

        Note that the id may not necessarily be unique outside of depth=0.
        """
        return " ".join(self.args)

    def create_block(self):
        """If not existent yet, create an empty block that can accept new fields.

        After this operation, c.fields will always return a FieldCollection
        instead of None.
        Return self to allow further chaining."""
        if "block" not in self.data:
            self.data["block"] = {}

    def delete_block(self):
        """Remove a block with any contents from the field, leaving only args."""
        self.data.pop("block", "")

    def __eq__(self, other: Field):
        return other.data is self.data

    def __repr__(self):
        suffix = " {..}" if self.fields else ""
        return f"<{self.__class__.__name__} id {id(self)}: {self.id}{suffix}>"


class TopLevelField(Field):
    # TODO: Move NONAME recognition here OR add blank 'type' and 'name' to comment blocks in parser.py
    @property
    def module(self) -> str:
        return self.data["directive"]

    @property
    def type(self) -> Optional[str]:
        # Comments don't have a field 'type'
        return self.data["type"] if "type" in self.data else None

    @property
    def name(self) -> Optional[str]:
        # Comments don't have a field 'name'
        return self.data["name"] if "name" in self.data else None

    @property
    def key(self) -> str:
        """Get a key - all arguments as a top level field."""
        # For top level items, the whole directive + args consitute a key
        return self.id


class FieldCollection:
    def __init__(
        self, block: dict, parent: Union[Field, Config], field_class: type = Field
    ):
        self.data = block
        self.parent = parent
        self.field_cls = field_class

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
        raise KeyError("Requested field not found.")

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
        raise KeyError("Pattern not found.")

    def get_all_re(self, regex: str) -> Iterable[Field]:
        """Return a generator of all elements matching the pattern."""
        r = re.compile(regex)
        for field in self.all():
            if re.match(r, field.id):
                yield field

    def all(self) -> Iterable[Field]:
        """Return a generator of all non-comment elements."""
        for item in self.data:
            if not item["directive"].startswith("#"):
                yield self.field_cls(item, self)

    def add(self, args: Iterable[str] = None, block: bool = False) -> Field:
        """Add a new field to this collection.

          args - the list of arguments defining the field. If none, the field
        will be treated as an unnamed one.
          block - whether to initialize an empty { } block inside the field

        Examples:
        c.fields.add(('ltm', 'pool', '/Common/pool'), True)
        pool.fields.add(('monitor', '/Common/monitor'))
        """
        # TODO: type and name for top level fields?
        args = args or []
        d = {
            "directive": args[0] if args else "_unnamed",
            "args": list(args[1:]) if len(args) > 1 else [],
        }
        if block:
            d["block"] = {}
        field = Field(d, self)
        self.data.append(d)
        return field

    def remove(self, field: Field):
        """Remove the given field from the collection."""
        self.data.remove(field.data)

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
