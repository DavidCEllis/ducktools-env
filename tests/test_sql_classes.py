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
from unittest import mock
import typing
import types

import pytest

# noinspection PyProtectedMember
from ducktools.env._sqlclasses import (
    _laz,
    TYPE_MAP,
    MAPPED_TYPES,
    SQLContext,
    SQLAttribute,
    SQLClass,

    get_sql_fields,
    flatten_list,
    separate_list,
    caps_to_snake,
)


def test_type_map():
    # Check that the MAPPED_TYPES matches the union of types in TYPE_MAP
    union = None
    for t in TYPE_MAP.keys():
        union = typing.Union[union, t]

    assert MAPPED_TYPES == union


class TestListFlattenSeparate:
    def test_flatten(self):
        l = ['a', 'b', 'c']
        assert flatten_list(l) == "a;b;c"

    def test_separate(self):
        l = "a;b;c"
        assert separate_list(l) == ['a', 'b', 'c']


def test_caps_to_snake():
    assert caps_to_snake("CapsNamedClass") == "caps_named_class"


def test_sql_context():
    with mock.patch.object(_laz.sql, "connect") as sql_connect:
        connection_mock = mock.MagicMock()
        sql_connect.return_value = connection_mock

        with SQLContext("FakeDB") as con:
            assert con is connection_mock

        sql_connect.assert_called_once_with("FakeDB")
        connection_mock.close.assert_called()


def test_sql_attribute():
    attrib = SQLAttribute(primary_key=True, unique=False, internal=False, computed=None)
    assert attrib.primary_key is True
    assert attrib.unique is False
    assert attrib.internal is False
    assert attrib.computed is None

    with pytest.raises(AttributeError):
        # This currently raises an error to avoid double specifying
        attrib = SQLAttribute(primary_key=True, unique=True)


class SharedExample:
    @property
    def example_class(self):
        class ExampleClass(SQLClass):
            uid: int = SQLAttribute(default=None, primary_key=True)
            name: str = SQLAttribute(unique=True)
            age: int = SQLAttribute(default=20, internal=True)
            height_m: float
            height_feet: float = SQLAttribute(default=None, computed="height_m * 3.28084")
            friends: list[str] = SQLAttribute(default_factory=list)
            some_bool: bool

        return ExampleClass

    @property
    def field_dict(self):
        return {
            "uid": SQLAttribute(default=None, primary_key=True, type=int),
            "name": SQLAttribute(unique=True, type=str),
            "age": SQLAttribute(default=20, internal=True, type=int),
            "height_m": SQLAttribute(type=float),
            "height_feet": SQLAttribute(default=None, computed="height_m * 3.28084", type=float),
            "friends": SQLAttribute(default_factory=list, type=list[str]),
            "some_bool": SQLAttribute(type=bool),
        }


class TestClassConstruction(SharedExample):
    """
    Test that the basic class features are built correctly
    """

    def test_table_features(self):
        ex_cls = self.example_class
        assert ex_cls.PK_NAME == "uid"
        assert ex_cls.TABLE_NAME == "example_class"

    def test_get_sql_fields(self):
        fields = get_sql_fields(self.example_class)
        assert fields == self.field_dict

    def test_valid_fields(self):
        valid_fields = self.field_dict
        valid_fields.pop("age")  # Internal only field should be excluded
        assert valid_fields == self.example_class.VALID_FIELDS

    def test_computed_fields(self):
        assert self.example_class.COMPUTED_FIELDS == {"height_feet"}

    def test_str_list_columns(self):
        assert self.example_class.STR_LIST_COLUMNS == {"friends"}

    def test_bool_columns(self):
        assert self.example_class.BOOL_COLUMNS == {"some_bool"}


class TestSQLGeneration(SharedExample):
    """
    Test that the generated SQL looks correct
    """
    def test_create_table(self):
        mock_con = mock.MagicMock()
        self.example_class.create_table(mock_con)

        mock_con.execute.assert_called_with(
            "CREATE TABLE IF NOT EXISTS example_class("
            "uid INTEGER PRIMARY KEY, "
            "name TEXT UNIQUE, "
            "height_m REAL, "
            "height_feet REAL GENERATED ALWAYS AS (height_m * 3.28084), "
            "friends TEXT, "  # list[str] is converted to TEXT
            "some_bool INTEGER"  # Bools are converted to INTEGERS
            ")"
        )

    def test_drop_table(self):
        mock_con = mock.MagicMock()
        self.example_class.drop_table(mock_con)

        mock_con.execute.assert_called_with("DROP TABLE IF EXISTS example_class")

    def test_select_rows_no_filters(self):
        mock_con = mock.MagicMock()
        mock_cursor = mock.MagicMock()
        mock_rows = mock.MagicMock()
        mock_fetchall = mock.MagicMock()

        mock_con.cursor.return_value = mock_cursor
        mock_cursor.execute.return_value = mock_rows
        mock_rows.fetchall.return_value = mock_fetchall

        row_out = self.example_class.select_rows(mock_con)
        assert row_out is mock_fetchall

        mock_rows.fetchall.assert_called_once()
        mock_cursor.execute.assert_called_once_with(
            "SELECT * FROM example_class",
            {}
        )
        mock_con.cursor.assert_called_once()
        mock_cursor.close.assert_called_once()

    def test_select_row_no_filters(self):
        mock_con = mock.MagicMock()
        mock_cursor = mock.MagicMock()
        mock_rows = mock.MagicMock()
        mock_fetchone = mock.MagicMock()

        mock_con.cursor.return_value = mock_cursor
        mock_cursor.execute.return_value = mock_rows
        mock_rows.fetchone.return_value = mock_fetchone

        row_out = self.example_class.select_row(mock_con)
        assert row_out is mock_fetchone

        mock_rows.fetchone.assert_called_once()
        mock_cursor.execute.assert_called_once_with(
            "SELECT * FROM example_class",
            {}
        )
        mock_con.cursor.assert_called_once()
        mock_cursor.close.assert_called_once()

    def test_select_rows_filters(self):
        mock_con = mock.MagicMock()
        mock_cursor = mock.MagicMock()
        mock_rows = mock.MagicMock()
        mock_fetchall = mock.MagicMock()

        mock_con.cursor.return_value = mock_cursor
        mock_cursor.execute.return_value = mock_rows
        mock_rows.fetchall.return_value = mock_fetchall

        row_out = self.example_class.select_rows(mock_con, {"name": "John"})
        assert row_out is mock_fetchall

        mock_rows.fetchall.assert_called_once()
        mock_cursor.execute.assert_called_once_with(
            "SELECT * FROM example_class WHERE name = :name",
            {"name": "John"}
        )
        mock_con.cursor.assert_called_once()
        mock_cursor.close.assert_called_once()

    def test_select_row_invalid_filter(self):
        mock_con = mock.MagicMock()

        with pytest.raises(KeyError):
            self.example_class.select_rows(mock_con, {"NotAField": 42})

    def test_select_rows_like(self):
        mock_con = mock.MagicMock()
        mock_cursor = mock.MagicMock()
        mock_rows = mock.MagicMock()
        mock_fetchall = mock.MagicMock()

        mock_con.cursor.return_value = mock_cursor
        mock_cursor.execute.return_value = mock_rows
        mock_rows.fetchall.return_value = mock_fetchall

        row_out = self.example_class.select_like(mock_con, {"name": "John"})
        assert row_out is mock_fetchall

        mock_rows.fetchall.assert_called_once()
        mock_cursor.execute.assert_called_once_with(
            "SELECT * FROM example_class WHERE name LIKE :name",
            {"name": "John"}
        )
        mock_con.cursor.assert_called_once()
        mock_cursor.close.assert_called_once()

    def test_select_rows_like_empty(self):
        mock_con = mock.MagicMock()
        mock_cursor = mock.MagicMock()
        mock_rows = mock.MagicMock()
        mock_fetchall = mock.MagicMock()

        mock_con.cursor.return_value = mock_cursor
        mock_cursor.execute.return_value = mock_rows
        mock_rows.fetchall.return_value = mock_fetchall

        row_out = self.example_class.select_like(mock_con, {})
        assert row_out is mock_fetchall

        mock_rows.fetchall.assert_called_once()
        mock_cursor.execute.assert_called_once_with(
            "SELECT * FROM example_class",
            {}
        )
        mock_con.cursor.assert_called_once()
        mock_cursor.close.assert_called_once()

    def test_select_like_invalid_filter(self):
        mock_con = mock.MagicMock()

        with pytest.raises(KeyError):
            self.example_class.select_like(mock_con, {"NotAField": "*John"})

    def test_max_pk(self):
        mock_con = mock.MagicMock()
        mock_result = mock.MagicMock()
        mock_con.execute.return_value = mock_result

        max_pk = self.example_class.max_pk(mock_con)

        mock_con.execute.assert_called_with("SELECT MAX(uid) FROM example_class")
        mock_result.fetchone.assert_called()

    def test_row_from_pk(self):
        mock_con = mock.MagicMock()
        mock_cursor = mock.MagicMock()
        mock_con.cursor.return_value = mock_cursor

        row = self.example_class.row_from_pk(mock_con, 42)

        mock_cursor.execute.assert_called_once_with(
            "SELECT * FROM example_class WHERE uid = :uid",
            {"uid": 42},
        )
        mock_cursor.close.assert_called_once()

    def test_insert_row(self):
        mock_con = mock.MagicMock()

        result_row = mock.MagicMock()
        mock_con.execute.return_value = result_row
        result_row.lastrowid = 100

        ExampleClass = self.example_class
        ex = ExampleClass(
            name="John",
            age=42,
            height_m=1.0,
            some_bool=False,
        )

        assert ex.uid is None
        assert ex.height_feet is None

        with mock.patch.object(ExampleClass, "row_from_pk") as computed_check:
            return_row = types.SimpleNamespace(height_feet=6.0)
            computed_check.return_value = return_row

            ex.insert_row(mock_con)

        # Check the values were correctly updated
        assert ex.uid == ex.primary_key == 100
        assert ex.height_feet == 6.0

        # Check the call
        mock_con.execute.assert_called_with(
            "INSERT INTO example_class VALUES(:uid, :name, :height_m, :friends, :some_bool)",
            {
                "uid": None,
                "name": "John",
                "height_m": 1.0,
                "friends": "",
                "some_bool": False,
            }
        )

    def test_update_row(self):
        ExampleClass = self.example_class
        ex = ExampleClass(
            uid=1,
            name="John",
            age=42,
            height_m=1.0,
            some_bool=True,
        )

        mock_con = mock.MagicMock()

        with mock.patch.object(ExampleClass, "row_from_pk") as computed_check:
            return_row = types.SimpleNamespace(height_feet=6.0)
            computed_check.return_value = return_row

            ex.update_row(mock_con, ["some_bool"])

        assert ex.height_feet == 6.0

        mock_con.execute.assert_called_with(
            "UPDATE example_class SET some_bool = :some_bool WHERE uid = :uid",
            {
                "uid": 1,
                "name": "John",
                "height_m": 1.0,
                "friends": "",
                "some_bool": True,
            }
        )

    def test_update_row_invalid(self):
        ExampleClass = self.example_class
        ex = ExampleClass(
            uid=1,
            name="John",
            age=42,
            height_m=1.0,
            some_bool=True,
        )

        mock_con = mock.MagicMock()

        with pytest.raises(ValueError):
            ex.update_row(mock_con, ["NotAField"])

    def test_update_row_fail_no_pk(self):
        ExampleClass = self.example_class
        ex = ExampleClass(
            uid=None,
            name="John",
            age=42,
            height_m=1.0,
            some_bool=True,
        )

        mock_con = mock.MagicMock()

        with pytest.raises(AttributeError):
            ex.update_row(mock_con, ["some_bool"])

    def test_delete_row(self):
        ExampleClass = self.example_class
        ex = ExampleClass(
            uid=1,
            name="John",
            age=42,
            height_m=1.0,
            some_bool=True,
        )

        mock_con = mock.MagicMock()

        ex.delete_row(mock_con)

        mock_con.execute.assert_called_with(
            "DELETE FROM example_class WHERE uid = :uid",
            {"uid": 1},
        )

    def test_delete_row_before_set(self):
        ExampleClass = self.example_class
        ex = ExampleClass(
            uid=None,
            name="John",
            age=42,
            height_m=1.0,
            some_bool=True,
        )

        mock_con = mock.MagicMock()

        with pytest.raises(AttributeError):
            ex.delete_row(mock_con)


class TestSQLExecution(SharedExample):
    """
    Test that the generated SQL actually does what we expect.
    """
    def test_table_create_drop(self):
        ExampleClass = self.example_class
        context = SQLContext(":memory:")
        with context as con:
            # Table doesn't exist
            cursor = con.cursor()
            try:
                result = con.execute(
                    "SELECT name FROM sqlite_schema WHERE type = 'table' AND name = :name",
                    {"name": ExampleClass.TABLE_NAME},
                )
                row = result.fetchone()
            finally:
                cursor.close()

            assert row is None

            # Create the Table
            ExampleClass.create_table(con)

            # Now it should be in the schema
            cursor = con.cursor()
            try:
                result = con.execute(
                    "SELECT name FROM sqlite_schema WHERE type = 'table' AND name = :name",
                    {"name": ExampleClass.TABLE_NAME},
                )
                row = result.fetchone()
            finally:
                cursor.close()

            assert row[0] == "example_class"

            # Drop the table
            ExampleClass.drop_table(con)

            cursor = con.cursor()
            try:
                result = con.execute(
                    "SELECT name FROM sqlite_schema WHERE type = 'table' AND name = :name",
                    {"name": ExampleClass.TABLE_NAME},
                )
                row = result.fetchone()
            finally:
                cursor.close()

            assert row is None

    def test_create_table_row_retrieve(self):
        ExampleClass = self.example_class
        context = SQLContext(":memory:")
        with context as con:
            ExampleClass.create_table(con)

            ex = ExampleClass(
                name="John",
                height_m=1.0,
                some_bool=True,
            )

            ex.insert_row(con)

            ex_retrieved = ExampleClass.row_from_pk(con, ex.primary_key)

            assert ex == ex_retrieved

            ex.delete_row(con)

            ex_retrieved = ExampleClass.row_from_pk(con, ex.primary_key)
            assert ex_retrieved is None

    def test_select_row_rows(self):
        ExampleClass = self.example_class
        context = SQLContext(":memory:")
        with context as con:
            ExampleClass.create_table(con)

            ex = ExampleClass(
                name="John",
                height_m=1.0,
                some_bool=True,
            )

            ex.insert_row(con)

            ex_retrieved = ExampleClass.select_row(con, {"name": "John"})

            assert ex_retrieved == ex

            ex_retrieved = ExampleClass.select_rows(con, {"name": "John"})[0]

            assert ex_retrieved == ex

    def test_select_missing_row_rows(self):
        ExampleClass = self.example_class
        context = SQLContext(":memory:")
        with context as con:
            ExampleClass.create_table(con)


class TestIncorrectConstruction:
    def test_failed_class_pk(self):
        with pytest.raises(AttributeError):
            class ExampleClass(SQLClass):
                name: str = SQLAttribute(unique=True)
                age: int = SQLAttribute(internal=True)
                height_m: float
                height_feet: float = SQLAttribute(computed="height_m * 3.28084")
                friends: list[str] = SQLAttribute(default_factory=list)
                some_bool: bool

    def test_failed_class_double_pk(self):
        with pytest.raises(AttributeError):
            class ExampleClass(SQLClass):
                uid: int = SQLAttribute(primary_key=True)
                ununiqueid: int = SQLAttribute(primary_key=True)
                name: str = SQLAttribute(unique=True)
                age: int = SQLAttribute(internal=True)
                height_m: float
                height_feet: float = SQLAttribute(computed="height_m * 3.28084")
                friends: list[str] = SQLAttribute(default_factory=list)
                some_bool: bool

