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
from datetime import datetime, timedelta

import unittest.mock as mock
from pathlib import Path

import pytest

from ducktools.env.catalogue import BaseCatalogue, TempCatalogue, TemporaryEnv
from ducktools.env.catalogue import _laz  # noqa


@pytest.fixture
def mock_save():
    # Mock the .save() function from BaseCatalogue
    with mock.patch.object(BaseCatalogue, "save") as save_func:
        yield save_func


@pytest.fixture
def mock_subprocess():
    # Subprocess module lives in the _laz object
    with mock.patch.object(_laz, "subprocess") as subprocess_obj:
        yield subprocess_obj


@pytest.fixture(scope="function")
def fake_temp_envs(catalogue_path):
    env_0_path = str(Path(catalogue_path).parent / "env_0")
    env_1_path = str(Path(catalogue_path).parent / "env_1")
    python_path = sys.executable

    # ENV examples based on examples folder
    env_0 = TemporaryEnv(
        name="env_0",
        path=env_0_path,
        python_version="3.12.5",
        parent_python=python_path,
        created_on="2024-09-02T14:55:53.102038",
        last_used="2024-09-02T14:55:53.102038",
        spec_hashes=["6986c6ae4a2965a4456333b8c60c5ac923ddca0d7edaa70b36b50f545ed8b24b"],
        installed_modules=[
            "certifi==2024.8.30",
            "charset-normalizer==3.3.2",
            "idna==3.8",
            "markdown-it-py==3.0.0",
            "mdurl==0.1.2",
            "pygments==2.18.0",
            "requests==2.32.3",
            "rich==13.8.0",
            "urllib3==2.2.2",
        ]
    )

    env_1 = TemporaryEnv(
        name="env_1",
        path=env_1_path,
        python_version="3.12.5",
        parent_python=python_path,
        created_on="2024-09-02T14:55:58.827666",
        last_used="2024-09-02T14:55:58.827666",
        spec_hashes=["85cdf5c0f9b109ba70cd936b153fd175307406eb802e05df453d5ccf5a19383f"],
        installed_modules=["cowsay==6.1"],
    )

    return {"env_0": env_0, "env_1": env_1}

@pytest.fixture(scope="function")
def fake_temp_catalogue(catalogue_path, fake_temp_envs):
    cat = TempCatalogue(
        path=catalogue_path,
        environments=fake_temp_envs,
        env_counter=2,
    )

    yield cat


@pytest.mark.usefixtures("mock_save")
class TestTempCatalogue:
    def test_delete_env(self, fake_temp_catalogue, fake_temp_envs, mock_save):
        with mock.patch.object(_laz, "shutil") as shutil_patch:
            rmtree = mock.MagicMock()
            shutil_patch.rmtree = rmtree

            pth = fake_temp_envs["env_0"].path

            fake_temp_catalogue.delete_env("env_0")

            rmtree.assert_called_once_with(pth)

            mock_save.assert_called()

            assert "env_0" not in fake_temp_catalogue.environments

    def test_delete_nonexistent_env(self, fake_temp_catalogue):
        with mock.patch.object(_laz, "shutil"):
            with pytest.raises(FileNotFoundError):
                fake_temp_catalogue.delete_env("env_42")

    def test_purge_folder(self, fake_temp_catalogue, fake_temp_envs):
        with mock.patch.object(_laz, "shutil") as shutil_patch:
            rmtree = mock.MagicMock()
            shutil_patch.rmtree = rmtree

            fake_temp_catalogue.purge_folder()
            rmtree.assert_called_once_with(fake_temp_catalogue.catalogue_folder)

        assert fake_temp_catalogue.environments == {}
        
    def test_oldest_cache(self, fake_temp_catalogue):
        assert fake_temp_catalogue.oldest_cache == "env_0"

        # "Use" env_0
        fake_temp_catalogue.environments["env_0"].last_used = datetime.now().isoformat()
        
        assert fake_temp_catalogue.oldest_cache == "env_1"

        # Empty catalogue returns None as oldest cache
        fake_temp_catalogue.environments = {}

        assert fake_temp_catalogue.oldest_cache is None

    def test_expire_caches(self, fake_temp_catalogue, mock_save):
        with mock.patch.object(fake_temp_catalogue, "delete_env") as del_env:
            # Expire all caches
            fake_temp_catalogue.expire_caches(timedelta(seconds=1))

            calls = [
                mock.call("env_0"),
                mock.call("env_1"),
            ]

            del_env.assert_has_calls(calls)

        mock_save.assert_called_once()