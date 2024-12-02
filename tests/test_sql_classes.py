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

import pytest

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
    mapped_type_construct = typing.Union[*TYPE_MAP.keys()]
    assert MAPPED_TYPES == mapped_type_construct


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


class TestWithExample:
    @property
    def example_class(self):
        class ExampleClass(SQLClass):
            uid: int = SQLAttribute(primary_key=True)
            name: str = SQLAttribute(unique=True)
            age: int = SQLAttribute(internal=True)
            height_m: float
            height_feet: float = SQLAttribute(computed="height_m * 3.28084")
            friends: list[str] = SQLAttribute(default_factory=list)
            some_bool: bool

        return ExampleClass

    @property
    def field_dict(self):
        return {
            "uid": SQLAttribute(primary_key=True, type=int),
            "name": SQLAttribute(unique=True, type=str),
            "age": SQLAttribute(internal=True, type=int),
            "height_m": SQLAttribute(type=float),
            "height_feet": SQLAttribute(computed="height_m * 3.28084", type=float),
            "friends": SQLAttribute(default_factory=list, type=list[str]),
            "some_bool": SQLAttribute(type=bool),
        }

    def test_table_features(self):
        ex_cls = self.example_class
        assert ex_cls.PRIMARY_KEY == "uid"
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


def test_failed_class_pk():
    with pytest.raises(AttributeError):
        class ExampleClass(SQLClass):
            name: str = SQLAttribute(unique=True)
            age: int = SQLAttribute(internal=True)
            height_m: float
            height_feet: float = SQLAttribute(computed="height_m * 3.28084")
            friends: list[str] = SQLAttribute(default_factory=list)
            some_bool: bool


def test_failed_class_double_pk():
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

