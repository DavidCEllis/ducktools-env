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

import os
import os.path
import sqlite3
import tempfile

from unittest import mock

import pytest

from ducktools.env._sqlclasses import SQLClass
from ducktools.env.register import RegisteredScript, RegisterManager
from ducktools.env.exceptions import ScriptNotFound


@pytest.fixture(scope="function")
def test_register():
    base_folder = os.path.join(os.path.dirname(__file__), "testing_data")
    with tempfile.TemporaryDirectory(dir=base_folder) as tempdir:
        register_db = os.path.join(tempdir, "register.db")
        register = RegisterManager(path=register_db)
        yield register


class TestRegisterManager:
    def test_connection_new(self, test_register):
        with (
            mock.patch("os.path.exists", return_value=False) as exists_mock,
            mock.patch("os.makedirs") as makedirs_mock,
            mock.patch.object(SQLClass, "create_table") as create_table_mock,
        ):
            con = test_register.connection

            assert con.db == test_register.path

            exists_mock.assert_called_with(test_register.path)
            makedirs_mock.assert_called_with(os.path.dirname(test_register.path), exist_ok=True)
            create_table_mock.assert_called()

    def test_add_remove_retrieve_script(self, test_register):
        # Create the table before putting the mock in place
        with test_register.connection:
            pass

        script_path = "path/to/script.py"
        script_name = "script"

        with (
            mock.patch("os.path.exists", return_value=True),
            mock.patch("os.path.abspath", side_effect=lambda x: x) as abspath_mock,
        ):
            row = test_register.add_script(script_path)

            assert row.name == script_name
            assert row.path == script_path

            abspath_mock.assert_called_once_with(script_path)

            # Retrieve the row
            retrieve_row = test_register.retrieve_script(script_name)

            assert retrieve_row == row

            # Delete the row and confirm it is no longer retrievable
            test_register.remove_script(script_name)
            with pytest.raises(ScriptNotFound):
                test_register.retrieve_script(script_name)

    def test_add_script_not_found(self, test_register):
        with test_register.connection:
            with pytest.raises(FileNotFoundError):
                test_register.add_script("path/to/nonexistent/script.py")

    def test_add_repeated_script(self, test_register):
        with test_register.connection:
            pass

        script_path = "path/to/script.py"

        with (
            mock.patch("os.path.exists", return_value=True),
            mock.patch("os.path.abspath", side_effect=lambda x: x) as abspath_mock,
        ):
            test_register.add_script(script_path)

            with pytest.raises(RuntimeError):
                test_register.add_script(script_path)

    def test_retrieve_lost_script(self, test_register):
        # Create the table before putting the mock in place
        with test_register.connection:
            pass

        script_path = "path/to/script.py"
        script_name = "script"

        with (
            mock.patch("os.path.exists", return_value=True),
            mock.patch("os.path.abspath", side_effect=lambda x: x) as abspath_mock,
        ):
            test_register.add_script(script_path)

        # Now unpatched the script should not exist and the script should error
        with pytest.raises(FileNotFoundError):
            test_register.retrieve_script(script_name)

    def test_list_registered_scripts(self, test_register):
        # Create the table before putting the mock in place
        with test_register.connection:
            pass

        script_path = "path/to/script.py"
        script2_path = "path/to/script2.py"
        script3_path = "path/to/script3.py"

        with (
            mock.patch("os.path.exists", return_value=True),
            mock.patch("os.path.abspath", side_effect=lambda x: x),
        ):
            script = test_register.add_script(script_path)
            script2 = test_register.add_script(script2_path)
            script3 = test_register.add_script(script3_path)

            scripts = test_register.list_registered_scripts()

            assert scripts == [script, script2, script3]
