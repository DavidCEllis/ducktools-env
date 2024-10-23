# ducktools.env
# MIT License
# 
# Copyright (c) 2024 David C Ellis
# 
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
# 
# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.
# 
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.

# This is a minimal object/database wrapper for ducktools.classbuilder
# Execute the class to see examples of the methods that will be generated

import itertools

from ducktools.lazyimporter import LazyImporter, ModuleImport

from ducktools.classbuilder import (
    SlotMakerMeta,
    builder,
    make_unified_gatherer,
)

from ducktools.classbuilder.prefab import (
    PREFAB_FIELDS,
    Attribute,
    as_dict,
    eq_maker,
    get_attributes,
    init_maker,
    repr_maker,
)


# Unlike the other modules this has its own lazy importer
# As it might be spun off as a separate package
_laz = LazyImporter(
    [
        ModuleImport("sqlite3", asname="sql")
    ]
)


TYPE_MAP = {
    None: "NULL",
    int: "INTEGER",
    bool: "INTEGER",
    float: "REAL",
    str: "TEXT",
    str | None: "TEXT",
    bytes: "BLOB",
    list[str]: "TEXT"  # lists of strings are converted to delimited strings
}

MAPPED_TYPES = None | int | bool | float | str | bytes | list[str]


class SQLContext:
    """
    A simple context manager to handle SQLite database connections
    """
    def __init__(self, db):
        self.db = db
        self.connection = None

    def __enter__(self):
        self.connection = _laz.sql.connect(self.db)
        return self.connection

    def __exit__(self, exc_type, exc_val, exc_tb):
        if self.connection is not None:
            self.connection.close()
            self.connection = None


class SQLAttribute(Attribute):
    """
    A Special attribute for SQL tables

    :param unique: Should this field be unique in the table
    :param internal: Should this field be excluded from the table
    """
    primary_key: bool = False
    unique: bool = False
    internal: bool = False
    computed: str | None = None

    def validate_field(self):
        super().validate_field()
        if self.primary_key and self.unique:
            raise AttributeError("Primary key fields are already unique")


def get_sql_fields(cls: "SQLMeta") -> dict[str, SQLAttribute]:
    return get_attributes(cls)  # noqa


unified_gatherer = make_unified_gatherer(SQLAttribute)


def flatten_list(strings: list[str], *, delimiter=";") -> str:
    return delimiter.join(strings)


def separate_list(string: str, *, delimiter=";") -> list[str]:
    return string.split(delimiter) if string else []


def caps_to_snake(name: str):
    letters = [name[0].lower()]
    for previous, current in itertools.pairwise(name):
        if current.isupper() and not previous.isupper():
            letters.append("_")
        letters.append(current.lower())
    return "".join(letters)


class SQLMeta(SlotMakerMeta):
    TABLE_NAME: str
    VALID_FIELDS: dict[str, SQLAttribute]
    COMPUTED_FIELDS: set[str]
    PRIMARY_KEY: str
    STR_LIST_COLUMNS: set[str]
    BOOL_COLUMNS: set[str]


default_methods = frozenset({init_maker, repr_maker, eq_maker})


class SQLClass(metaclass=SQLMeta):
    _meta_gatherer = unified_gatherer
    __slots__ = {}

    def __init_subclass__(
        cls,
        *,
        methods=default_methods,
        gatherer=unified_gatherer,
        **kwargs,
    ):
        slots = "__slots__" in cls.__dict__
        builder(cls, gatherer=gatherer, methods=methods, flags={"slotted": slots, "kw_only": True})

        fields = get_sql_fields(cls)
        valid_fields = {}
        split_columns = set()
        bools = set()
        computed_fields = set()

        for name, value in fields.items():
            if value.computed:
                computed_fields.add(name)
            if not value.internal:
                valid_fields[name] = value

            if value.type == list[str]:
                split_columns.add(name)
            elif value.type is bool:
                bools.add(name)

        cls.VALID_FIELDS = valid_fields
        cls.COMPUTED_FIELDS = computed_fields
        cls.STR_LIST_COLUMNS = split_columns
        cls.BOOL_COLUMNS = bools

        setattr(cls, PREFAB_FIELDS, list(fields.keys()))

        primary_key = None
        for name, field in fields.items():
            if field.primary_key:
                primary_key = name
                break

        if primary_key is None:
            raise AttributeError("sqlclass *must* have one primary key")

        if sum(1 for f in fields.values() if f.primary_key) > 1:
            raise AttributeError("sqlclass *must* have **only** one primary key")

        cls.PRIMARY_KEY = primary_key
        cls.TABLE_NAME = caps_to_snake(cls.__name__)

        super().__init_subclass__(**kwargs)

    @classmethod
    def create_table(cls, con):
        sql_field_list = []

        for name, field in cls.VALID_FIELDS.items():
            field_type = TYPE_MAP[field.type]
            if field.primary_key:
                constraint = " PRIMARY KEY"
            elif field.unique:
                constraint = " UNIQUE"
            else:
                constraint = ""

            if field.computed:
                field_str = f"{name} {field_type}{constraint} GENERATED ALWAYS AS ({field.computed})"
            else:
                field_str = f"{name} {field_type}{constraint}"

            sql_field_list.append(field_str)

        field_info = ", ".join(sql_field_list)
        sql_command = f"CREATE TABLE IF NOT EXISTS {cls.TABLE_NAME}({field_info})"

        con.execute(sql_command)

    @classmethod
    def drop_table(cls, con):
        con.execute(f"DROP TABLE IF EXISTS {cls.TABLE_NAME}")

    @classmethod
    def row_factory(cls, cursor, row):
        fields = [column[0] for column in cursor.description]
        kwargs = {}
        for key, value in zip(fields, row, strict=True):
            if key in cls.STR_LIST_COLUMNS:
                kwargs[key] = separate_list(value)
            elif key in cls.BOOL_COLUMNS:
                kwargs[key] = bool(value)
            else:
                kwargs[key] = value

        return cls(**kwargs)  # noqa

    @classmethod
    def _select_query(cls, cursor, filters: dict[str, MAPPED_TYPES] | None = None):
        filters = {} if filters is None else filters

        if filters:
            keyfilter = []
            for key in filters.keys():
                if key not in cls.VALID_FIELDS:
                    raise KeyError(f"{key} is not a valid column for table {cls.TABLE_NAME}")

                keyfilter.append(f"{key} = :{key}")

            filter_str = ", ".join(keyfilter)
            search_condition = f" WHERE {filter_str}"
        else:
            search_condition = ""

        cursor.row_factory = cls.row_factory
        result = cursor.execute(f"SELECT * FROM {cls.TABLE_NAME} {search_condition}", filters)
        return result

    @classmethod
    def select_rows(cls, con, filters: dict[str, MAPPED_TYPES] | None = None):
        cursor = con.cursor()
        try:
            result = cls._select_query(cursor, filters=filters)
            rows = result.fetchall()
        finally:
            cursor.close()

        return rows

    @classmethod
    def select_row(cls, con, filters: dict[str, MAPPED_TYPES] | None = None):
        cursor = con.cursor()
        try:
            result = cls._select_query(cursor, filters=filters)
            row = result.fetchone()
        finally:
            cursor.close()

        return row

    @classmethod
    def select_like(cls, con, filters: dict[str, MAPPED_TYPES] | None = None):
        filters = {} if filters is None else filters

        if filters:
            keyfilter = []
            for key in filters.keys():
                if key not in cls.VALID_FIELDS:
                    raise KeyError(f"{key} is not a valid column for table {cls.TABLE_NAME}")

                keyfilter.append(f"{key} LIKE :{key}")

            filter_str = ", ".join(keyfilter)
            search_condition = f" WHERE {filter_str}"
        else:
            search_condition = ""

        cursor = con.cursor()
        try:
            cursor.row_factory = cls.row_factory
            result = cursor.execute(
                f"SELECT * FROM {cls.TABLE_NAME} {search_condition}",
                filters
            )
            rows = result.fetchall()
        finally:
            cursor.close()

        return rows

    @classmethod
    def max_pk(cls, con):
        statement = f"SELECT MAX({cls.PRIMARY_KEY}) from {cls.TABLE_NAME}"
        result = con.execute(statement)
        return result.fetchone()[0]

    @classmethod
    def row_from_pk(cls, con, pk_value):
        return cls.select_row(con, filters={cls.PRIMARY_KEY: pk_value})

    def insert_row(self, con):
        columns = ", ".join(
            f":{name}"
            for name in self.VALID_FIELDS.keys()
            if name not in self.COMPUTED_FIELDS
        )
        sql_statement = f"INSERT INTO {self.TABLE_NAME} VALUES({columns})"

        processed_values = {
            name: flatten_list(value) if isinstance(value, list) else value
            for name, value in as_dict(self).items()
            if name in self.VALID_FIELDS and name not in self.COMPUTED_FIELDS
        }

        with con:
            result = con.execute(sql_statement, processed_values)

            if getattr(self, self.PRIMARY_KEY) is None:
                setattr(self, self.PRIMARY_KEY, result.lastrowid)

            if self.COMPUTED_FIELDS:
                row = self.row_from_pk(con, result.lastrowid)
                for field in self.COMPUTED_FIELDS:
                    setattr(self, field, getattr(row, field))

    def update_row(self, con, columns: list[str]):
        if self.PRIMARY_KEY is None:
            raise AttributeError("Primary key has not yet been set")

        if invalid_columns := (set(columns) - self.VALID_FIELDS.keys()):
            raise ValueError(f"Invalid fields: {invalid_columns}")

        processed_values = {
            name: flatten_list(value) if isinstance(value, list) else value
            for name, value in as_dict(self).items()
            if name in self.VALID_FIELDS and name not in self.COMPUTED_FIELDS
        }

        set_columns = ", ".join(f"{name} = :{name}" for name in columns)
        search_condition = f"{self.PRIMARY_KEY} = :{self.PRIMARY_KEY}"

        with con:
            con.execute(
                f"UPDATE {self.TABLE_NAME} SET {set_columns} WHERE {search_condition}",
                processed_values,
            )

    def delete_row(self, con):
        if self.PRIMARY_KEY is None:
            raise AttributeError("Primary key has not yet been set")

        pk_filter = {self.PRIMARY_KEY: getattr(self, self.PRIMARY_KEY)}

        with con:
            con.execute(
                f"DELETE FROM {self.TABLE_NAME} WHERE {self.PRIMARY_KEY} = :{self.PRIMARY_KEY}",
                pk_filter,
            )
