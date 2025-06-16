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

import sys
import os.path
import tempfile

from ducktools.pythonfinder import get_python_installs
from ducktools.pythonfinder.shared import DetailFinder

from ducktools.env.catalogue import TemporaryCatalogue
from ducktools.env.config import Config

import ducktools.env.platform_paths as platform_paths

from unittest.mock import patch
import pytest


@pytest.fixture(scope="session")
def available_pythons():
    return get_python_installs()


@pytest.fixture(scope="session")
def this_python():
    py = sys.executable
    finder = DetailFinder()
    details = finder.get_install_details(py)
    # Pretend PyPy is CPython for tests
    if details.implementation == "pypy":
        details.implementation = "cpython"

    # Remove pre-release number from version!
    details.version = *details.version[:3], "release", 0
    return details


@pytest.fixture(scope="session", autouse=True)
def use_this_python_install(this_python):
    with patch("ducktools.env._lazy_imports.list_python_installs") as get_installs:
        get_installs.return_value = [this_python]
        yield


@pytest.fixture(scope="function")
def catalogue_path():
    """
    Provide a test folder path for python environments, delete after tests in a class have run.
    """
    base_folder = os.path.join(os.path.dirname(__file__), "testing_data")
    with tempfile.TemporaryDirectory(dir=base_folder) as folder:
        cache_file = os.path.join(folder, platform_paths.CATALOGUE_FILENAME)
        yield cache_file


@pytest.fixture(scope="session")
def test_config():
    config = Config(
        cache_maxcount=2,
        cache_lifetime=1/24,
    )
    yield config


@pytest.fixture(scope="function")
def testing_catalogue(catalogue_path):
    catalogue = TemporaryCatalogue(path=catalogue_path)
    yield catalogue


def pytest_report_header():
    return f"virtualenv: {sys.prefix}"
