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
import os.path

from ducktools.classbuilder.prefab import Prefab

from ._lazy_imports import laz as _laz
from ._sqlclasses import SQLAttribute, SQLClass, SQLContext
from .exceptions import ScriptNotFound


class RegisteredScript(SQLClass):
    rowid: int = SQLAttribute(default=None, primary_key=True)
    name: str = SQLAttribute(unique=True)
    path: str = SQLAttribute(unique=True)

    @classmethod
    def from_script(cls, relpath: str, script_name: str | None = None):
        if script_name is None:
            name = os.path.splitext(os.path.basename(relpath))[0]
        else:
            name = script_name
        path = os.path.abspath(relpath)
        return cls(name=name, path=path)


class RegisterManager(Prefab, kw_only=True):
    path: str

    @property
    def connection(self) -> SQLContext:
        if not os.path.exists(self.path):
            os.makedirs(os.path.dirname(self.path), exist_ok=True)
            with SQLContext(self.path) as con:
                RegisteredScript.create_table(con)

        return SQLContext(self.path)

    def add_script(
        self,
        script_path: str,
        script_name: str | None = None
    ) -> RegisteredScript:
        if not os.path.exists(script_path):
            raise FileNotFoundError(f"'{script_path}' not found")

        new_row = RegisteredScript.from_script(script_path, script_name=script_name)

        with self.connection as con:
            try:
                new_row.insert_row(con)
            except _laz.sql.DatabaseError as e:
                raise RuntimeError(
                    f"Could not add script: '{script_path}' to the register. SQL Error: {e}"
                )

        return new_row

    def retrieve_script(self, script_name: str) -> RegisteredScript:
        with self.connection as con:
            row_filter = {
                "name": script_name,
            }
            row = RegisteredScript.select_row(con, row_filter)

        if row is None:
            raise ScriptNotFound(
                f"'{script_name}' is not a registered script."
            )

        if not os.path.exists(row.path):
            with self.connection as con:
                row.delete_row(con)

            raise FileNotFoundError(
                f"'{script_name}' file at '{row.path} does not exist, removed from registry."
            )

        return row

    def remove_script(self, script_name: str) -> None:
        row = self.retrieve_script(script_name)

        with self.connection as con:
            row.delete_row(con)

    def list_registered_scripts(self) -> list[RegisteredScript]:
        with self.connection as con:
            rows = RegisteredScript.select_rows(con)

        return rows
