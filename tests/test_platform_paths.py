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

# Much of the code in platform_paths is platform dependent so don't expect
# 100% coverage with basic single platform testing.
import sys
from pathlib import Path

import unittest.mock as mock

from ducktools.env.platform_paths import ManagedPaths, USER_FOLDER, get_platform_folder


USER_PATH = Path(USER_FOLDER)


def test_get_platform_folder():
    platform_folder = get_platform_folder("demo")
    if sys.platform == "win32":
        assert platform_folder == str(USER_PATH / "demo")
    else:
        assert platform_folder == str(USER_PATH / ".demo")


class TestManagedPaths:
    project_name = "ducktools_testing"
    folder_base = get_platform_folder(project_name)
    paths = ManagedPaths(project_name)

    def test_basic_paths(self):
        # This test is to check all folder paths are correct and make sure
        # they are not accidentally changed.

        project_folder = Path(get_platform_folder(self.project_name)) / "env"

        assert self.paths.project_folder == str(project_folder)
        assert self.paths.config_path == str(project_folder / "config.json")
        assert self.paths.manager_folder == str(project_folder / "lib")
        assert self.paths.pip_zipapp == str(project_folder / "lib" / "pip.pyz")
        assert self.paths.env_folder == str(project_folder / "lib" / "ducktools-env")
        assert self.paths.application_folder == str(project_folder / "applications")
        assert self.paths.application_db == str(project_folder / "applications" / "app_catalogue.db")
        assert self.paths.cache_folder == str(project_folder / "caches")
        assert self.paths.cache_db == str(project_folder / "caches" / "catalogue.db")
        assert self.paths.build_base == str(project_folder / "build")

        if sys.platform == "win32":
            assert self.paths.uv_executable == str(project_folder / "lib" / "uv.exe")
        else:
            assert self.paths.uv_executable == str(project_folder / "lib" / "uv")

    def test_get_versions(self):
        with mock.patch.object(self.paths, "get_app_version") as gav_mock:
            gav_mock.return_value = "0.1.0"

            pip_ver = self.paths.get_pip_version()
            env_ver = self.paths.get_env_version()
            uv_ver = self.paths.get_uv_version()

            gav_mock.assert_has_calls(
                [
                    mock.call(f"{self.paths.pip_zipapp}.version"),
                    mock.call(f"{self.paths.env_folder}.version"),
                    mock.call(f"{self.paths.uv_executable}.version"),
                ]
            )

            assert pip_ver == env_ver == uv_ver == "0.1.0"

    def test_build_folder(self):
        with (
            mock.patch("tempfile.TemporaryDirectory") as tempdir_mock,
            mock.patch("os.makedirs") as makedirs_mock,
        ):
            tmpdir = "fake/temp/dir"
            tempdir_mock.return_value.__enter__.return_value = tmpdir

            with self.paths.build_folder() as fld:
                assert fld == tmpdir

            makedirs_mock.assert_called_once_with(
                self.paths.build_base,
                exist_ok=True,
            )

            tempdir_mock.assert_called_once_with(
                dir=self.paths.build_base
            )

    def test_get_app_version(self):
        with mock.patch("builtins.open") as open_mock:
            read_mock = mock.MagicMock(return_value="0.1.0")
            open_mock.return_value.__enter__.return_value.read = read_mock

            ver_path = "fake/versionfile"

            v = self.paths.get_app_version(ver_path)

            assert v == "0.1.0"

            read_mock.assert_called()
            open_mock.assert_called_with(ver_path, 'r')

    def test_get_app_version_fail(self):
        with mock.patch("builtins.open") as open_mock:
            open_mock.side_effect = FileNotFoundError()

            ver_path = "fake/versionfile"

            v = self.paths.get_app_version(ver_path)

            assert v is None

            open_mock.assert_called_with(ver_path, 'r')
