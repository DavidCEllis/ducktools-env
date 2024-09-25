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

import unittest.mock as mock

from ducktools.env import (
    FOLDER_ENVVAR, 
    DATA_BUNDLE_ENVVAR,
    DATA_BUNDLE_FOLDER,
    LAUNCH_PATH_ENVVAR, 
    LAUNCH_TYPE_ENVVAR
)
from ducktools.env.bundled_data import BundledDataError, ScriptData, get_data_folder
from ducktools.env._lazy_imports import laz

import pytest


@pytest.fixture
def temp_env_vars(monkeypatch):
    launch_path = "fake/launch/path"
    ducktools_folder = "path/to/ducktools"
    data_bundle = "data/bundle"
    data_dest_base = os.path.join(ducktools_folder, "tempdata")

    monkeypatch.setenv(LAUNCH_PATH_ENVVAR, launch_path)
    monkeypatch.setenv(FOLDER_ENVVAR, ducktools_folder)
    monkeypatch.setenv(DATA_BUNDLE_ENVVAR, data_bundle)

    yield launch_path, data_dest_base, data_bundle

@pytest.fixture
def temp_script_env_vars(monkeypatch, temp_env_vars):
    launch_type = "SCRIPT"
    monkeypatch.setenv(LAUNCH_TYPE_ENVVAR, launch_type)
    yield launch_type, *temp_env_vars


@pytest.fixture
def temp_bundle_env_vars(monkeypatch, temp_env_vars):
    launch_type = "BUNDLE"
    monkeypatch.setenv(LAUNCH_TYPE_ENVVAR, launch_type)
    yield launch_type, *temp_env_vars



class TestGetDataFolder:
    def test_no_envvar(self, monkeypatch):
        # Make sure env vars are missing
        monkeypatch.delenv(FOLDER_ENVVAR, raising=False)
        monkeypatch.delenv(DATA_BUNDLE_ENVVAR, raising=False)
        monkeypatch.delenv(LAUNCH_PATH_ENVVAR, raising=False)
        monkeypatch.delenv(LAUNCH_TYPE_ENVVAR, raising=False)

        with pytest.raises(BundledDataError) as err:
            get_data_folder()

        assert err.match(
            "^Environment variable .* not found, "
            "get_data_folder will only work with a "
            "bundled executable or script run"
        )

    def test_no_datavar(self, monkeypatch):
        monkeypatch.setenv(FOLDER_ENVVAR, "fake/folder")
        monkeypatch.setenv(LAUNCH_PATH_ENVVAR, "fake/launch/path")
        monkeypatch.setenv(LAUNCH_TYPE_ENVVAR, "SCRIPT")
        monkeypatch.delenv(DATA_BUNDLE_ENVVAR, raising=False)

        with pytest.raises(BundledDataError) as err:
            get_data_folder()

        assert err.match("No bundled data included with script .*")

    def test_success(self, temp_script_env_vars):
        launch_type, launch_path, data_dest_base, data_bundle = temp_script_env_vars
        
        scriptdata = get_data_folder()

        assert scriptdata == ScriptData(
            launch_type=launch_type, 
            launch_path=launch_path, 
            data_dest_base=data_dest_base, 
            data_bundle=data_bundle,
        )


class TestScriptData:
    def test_contextmanager_script(self, temp_script_env_vars):
        with (
            mock.patch.object(ScriptData, "_makedir_script") as script_mock,
            mock.patch.object(ScriptData, "_makedir_bundle") as bundle_mock,
            mock.patch.object(laz, "TemporaryDirectory") as tempdir_mock,
            mock.patch("os.makedirs") as makedirs_mock
        ):
            launch_type, launch_path, data_dest_base, data_bundle = temp_script_env_vars

            temp_folder_name = "fake/temporary/folder"

            temp_mock = mock.MagicMock()
            temp_mock.name = temp_folder_name

            tempdir_mock.return_value = temp_mock
            
            with ScriptData(launch_type, launch_path, data_dest_base, data_bundle) as sd:
                assert sd == temp_mock.name

            makedirs_mock.assert_called_with(data_dest_base, exist_ok=True)
            tempdir_mock.assert_called_with(dir=data_dest_base)

            script_mock.assert_called_with(temp_mock)
            bundle_mock.assert_not_called()

            temp_mock.cleanup.assert_called()

    def test_contextmanager_bundle(self, temp_bundle_env_vars):
        with (
            mock.patch.object(ScriptData, "_makedir_script") as script_mock,
            mock.patch.object(ScriptData, "_makedir_bundle") as bundle_mock,
            mock.patch.object(laz, "TemporaryDirectory") as tempdir_mock,
            mock.patch("os.makedirs") as makedirs_mock
        ):
            launch_type, launch_path, data_dest_base, data_bundle = temp_bundle_env_vars

            temp_folder_name = "fake/temporary/folder"

            temp_mock = mock.MagicMock()
            temp_mock.name = temp_folder_name

            tempdir_mock.return_value = temp_mock
            
            with ScriptData(launch_type, launch_path, data_dest_base, data_bundle) as sd:
                assert sd == os.path.join(temp_mock.name, DATA_BUNDLE_FOLDER)

            makedirs_mock.assert_called_with(data_dest_base, exist_ok=True)
            tempdir_mock.assert_called_with(dir=data_dest_base)

            script_mock.assert_not_called()
            bundle_mock.assert_called_with(temp_mock)

            temp_mock.cleanup.assert_called()

    def test_contextmanager_raises(self, temp_script_env_vars):
        with (
            mock.patch.object(ScriptData, "_makedir_script") as script_mock,
            mock.patch.object(ScriptData, "_makedir_bundle") as bundle_mock,
            mock.patch.object(laz, "TemporaryDirectory") as tempdir_mock,
            mock.patch("os.makedirs") as makedirs_mock
        ):
            launch_type, launch_path, data_dest_base, data_bundle = temp_script_env_vars

            temp_mock = mock.MagicMock()
            tempdir_mock.return_value = temp_mock
            
            script_mock.side_effect = Exception("FAILURE")

            with pytest.raises(Exception):
                with ScriptData(launch_type, launch_path, data_dest_base, data_bundle):
                    pass

            makedirs_mock.assert_called_with(data_dest_base, exist_ok=True)
            tempdir_mock.assert_called_with(dir=data_dest_base)

            script_mock.assert_called_with(temp_mock)
            bundle_mock.assert_not_called()

            # Cleanup is still called
            temp_mock.cleanup.assert_called()