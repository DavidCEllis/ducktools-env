# DuckTools-EnvMan
# Copyright (C) 2024 David C Ellis
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Lesser General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Lesser General Public License for more details.
#
# You should have received a copy of the GNU Lesser General Public License
# along with this program.  If not, see <https://www.gnu.org/licenses/>.

import sys
import os.path
import shutil

from ducktools.pythonfinder import get_python_installs
from ducktools.pythonfinder.shared import get_install_details

from ducktools.env.catalogue import TempCatalogue
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
    return get_install_details(py)


@pytest.fixture(scope="session", autouse=True)
def use_this_python_install(this_python):
    with patch("ducktools.env.catalogue._laz.list_python_installs") as get_installs:
        get_installs.return_value = [this_python]
        yield


@pytest.fixture(scope="function")
def catalogue_path():
    """
    Provide a test folder path for python environments, delete after tests in a class have run.
    """
    folder = os.path.join(os.path.dirname(__file__), "test_envs")
    cache_file = os.path.join(folder, platform_paths.CATALOGUE_FILENAME)
    yield cache_file
    try:
        shutil.rmtree(folder)
    except FileNotFoundError:
        pass


@pytest.fixture(scope="session")
def test_config():
    config = Config(
        cache_maxcount=2,
        cache_lifetime=1/24,
    )
    yield config


@pytest.fixture(scope="function")
def testing_catalogue(catalogue_path):
    catalogue = TempCatalogue(path=catalogue_path)
    yield catalogue
