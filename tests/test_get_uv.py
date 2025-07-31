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
import subprocess
import sys
import unittest.mock as mock
from pathlib import Path

import pytest

import ducktools.env.scripts.get_uv as get_uv
from ducktools.env.platform_paths import ManagedPaths

UV_PYTHON_LIST_OUTPUT = Path(__file__).parent / "data" / "uv_python_versions_list.txt"


@pytest.fixture(scope="function")
def block_local_uv():
    with mock.patch("shutil.which") as which_mock:
        which_mock.return_value = None
        yield


def test_get_available_pythons():
    uv_python_list_text = UV_PYTHON_LIST_OUTPUT.read_text()

    with mock.patch("subprocess.run") as run_mock:
        uv_path = "path/to/uv"

        data_mock = mock.MagicMock()
        data_mock.stdout = uv_python_list_text

        run_mock.return_value = data_mock

        uv_pythons = get_uv.get_available_pythons(uv_path=uv_path)

        run_mock.assert_called_once_with(
            [uv_path, "python", "list", "--all-versions"],
            capture_output=True,
            text=True,
            check=True,
        )

        available_pythons = [
            '3.13.0rc2',
            '3.12.5',
            '3.12.4',
            '3.12.3',
            '3.12.2',
            '3.12.1',
            '3.12.0',
            '3.11.9',
            '3.11.8',
            '3.11.7',
            '3.11.6',
            '3.11.5',
            '3.11.4',
            '3.11.3',
            '3.11.1',
            '3.10.14',
            '3.10.13',
            '3.10.12',
            '3.10.11',
            '3.10.9',
            '3.10.8',
            '3.10.7',
            '3.10.6',
            '3.10.5',
            '3.10.4',
            '3.10.3',
            '3.10.2',
            '3.10.0',
            '3.9.19',
            '3.9.18',
            '3.9.17',
            '3.9.16',
            '3.9.15',
            '3.9.14',
            '3.9.13',
            '3.9.12',
            '3.9.11',
            '3.9.10',
            '3.9.7',
            '3.9.6',
            '3.9.5',
            '3.9.4',
            '3.9.3',
            '3.9.2',
            '3.9.1',
            '3.9.0',
            '3.8.19',
            '3.8.18',
            '3.8.17',
            '3.8.16',
            '3.8.15',
            '3.8.14',
            '3.8.13',
            '3.8.12',
            '3.8.11',
            '3.8.10',
            '3.8.9',
            '3.8.8',
            '3.8.7',
            '3.8.6',
            '3.8.5',
            '3.8.3',
            '3.8.2',
            '3.7.9',
            '3.7.7',
            '3.7.6',
            '3.7.5',
            '3.7.4',
            '3.7.3',
        ]

        assert uv_pythons == available_pythons


def test_uv_install_python():
    with mock.patch("subprocess.run") as run_mock:
        uv_path = "path/to/uv"
        version_str = "3.12.6"

        get_uv.install_uv_python(uv_path=uv_path, version_str=version_str)

        run_mock.assert_called_once_with(
            [uv_path, "python", "install", version_str],
            check=True,
        )
