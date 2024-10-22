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
import sys
import tempfile
import unittest.mock as mock

from datetime import datetime, timedelta
from pathlib import Path

import pytest
from packaging.version import Version

from ducktools.env.catalogue import (
    BaseCatalogue,
    ApplicationCatalogue,
    TemporaryCatalogue,
    ApplicationEnvironment,
    TemporaryEnvironment,
)

from ducktools.env.config import Config
from ducktools.env.environment_specs import EnvironmentSpec
from ducktools.env.exceptions import PythonVersionNotFound
import ducktools.env.platform_paths as platform_paths


@pytest.fixture(scope="function")
def sql_catalogue_path():
    """
    Provide a test folder path for python environments, delete after tests in a class have run.
    """
    base_folder = os.path.join(os.path.dirname(__file__), "testing_data")
    os.makedirs(base_folder, exist_ok=True)
    with tempfile.TemporaryDirectory(dir=base_folder) as folder:
        cache_file = os.path.join(folder, platform_paths.CATALOGUE_FILENAME)
        yield cache_file


@pytest.fixture(scope="function")
def fake_temp_catalogue(sql_catalogue_path):
    cat = TemporaryCatalogue(
        path=sql_catalogue_path,
    )
    return cat


@pytest.fixture(scope="function")
def fake_temp_envs(fake_temp_catalogue):
    python_path = sys.executable
    python_version = ".".join(str(item) for item in sys.version_info[:3])

    # ENV examples based on examples folder
    env_0 = TemporaryEnvironment(
        row_id=0,
        root_path=fake_temp_catalogue.catalogue_folder,
        python_version=python_version,
        parent_python=python_path,
        created_on="2024-09-02T14:55:53.102038",
        last_used="2024-09-02T14:55:53.102038",
        completed=True,
        spec_hashes=["0caeabf94f2a523db4bb52752ef95067dd7e5c1e8f5b1e249dc37abdd1e60e1f"],
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

    env_1 = TemporaryEnvironment(
        row_id=1,
        root_path=fake_temp_catalogue.catalogue_folder,
        python_version=python_version,
        parent_python=python_path,
        created_on="2024-09-02T14:55:58.827666",
        last_used="2024-09-02T14:55:58.827666",
        completed=False,
        spec_hashes=["85cdf5c0f9b109ba70cd936b153fd175307406eb802e05df453d5ccf5a19383f"],
        installed_modules=["cowsay==6.1"],
    )

    env_2 = TemporaryEnvironment(
        row_id=2,
        root_path=fake_temp_catalogue.catalogue_folder,
        python_version=python_version,
        parent_python=python_path,
        created_on="2024-09-02T14:55:59.827666",
        last_used="2024-09-02T14:55:59.827666",
        completed=True,
        spec_hashes=["85cdf5c0f9b109ba70cd936b153fd175307406eb802e05df453d5ccf5a19383f"],
        installed_modules=["cowsay==6.1"],
    )

    env_3 = TemporaryEnvironment(
        row_id=3,
        root_path=fake_temp_catalogue.catalogue_folder,
        python_version=python_version,
        parent_python=python_path,
        created_on="2024-09-25T17:55:23.254577",
        last_used="2024-09-26T11:29:12.233691",
        completed=True,
        spec_hashes=["85cdf5c0f9b109ba70cd936b153fd175307406eb802e05df453d5ccf5a19383f"],
        lock_hash="840760dd5d911f145b94c72e670754391bf19c33d5272da7362b629c484fd1f6",
        installed_modules=["cowsay==6.1"],
    )

    # Add the environments to the catalogue so they get names and paths
    with fake_temp_catalogue.connection as con:
        env_0.insert_row(con)
        env_1.insert_row(con)
        env_2.insert_row(con)
        env_3.insert_row(con)

    return {"env_0": env_0, "env_1": env_1, "env_2": env_2, "env_3": env_3}


@pytest.fixture(scope="function")
def fake_full_catalogue(fake_temp_catalogue, fake_temp_envs):
    # By using fake_temp_envs the catalogue is populated
    return fake_temp_catalogue


@pytest.fixture
def fake_app_env(sql_catalogue_path):
    python_path = sys.executable
    python_version = ".".join(str(item) for item in sys.version_info[:3])

    # Env based on examples folder
    appname = "ducktools_testing/cowsay_example"
    env = ApplicationEnvironment(
        name=appname,
        path=str(Path(sql_catalogue_path).parent / "ducktools_testing/cowsay_example/env"),
        python_version=python_version,
        parent_python=python_path,
        created_on="2024-09-25T17:55:23.254577",
        last_used="2024-09-26T11:29:12.233691",
        completed=True,
        spec_hashes=[
            "226500066700d7910b3a57470f12f97ed402fe68b8b31fb592f0a76f7f0bd682"
        ],
        lock_hash="840760dd5d911f145b94c72e670754391bf19c33d5272da7362b629c484fd1f6",
        installed_modules=[
            "cowsay==6.1"
        ],
        owner="ducktools_testing",
        appname="cowsay_example",
        version="v0.1.0",
    )

    return env


# ENVIRONMENT TESTS

class TestTempEnv:
    @pytest.mark.parametrize("envname", ["env_0", "env_1", "env_2", "env_3"])
    def test_python_path(self, fake_temp_envs, envname, sql_catalogue_path):
        env = fake_temp_envs[envname]
        base_path = Path(sql_catalogue_path).parent

        if sys.platform == "win32":
            assert env.python_path == str(base_path / envname / "Scripts" / "python.exe")
        else:
            assert env.python_path == str(base_path / envname / "bin" / "python")

    @pytest.mark.skipif(sys.platform != "win32", reason="Windows only test")
    @pytest.mark.parametrize("envname", ["env_0", "env_1", "env_2", "env_3"])
    def test_python_path_windowed(self, fake_temp_envs, envname, sql_catalogue_path):
        # If there is no stdout on windows assume windowed executable
        with mock.patch("sys.stdout", new=None):
            env = fake_temp_envs[envname]
            base_path = Path(sql_catalogue_path).parent

            assert env.python_path == str(base_path / envname / "Scripts" / "pythonw.exe")

    def test_dates(self, fake_temp_envs):
        env_0 = fake_temp_envs["env_0"]
        assert env_0.last_used_simple == "2024-09-02 14:55:53"

        env_2 = fake_temp_envs["env_2"]
        assert env_2.last_used_simple == "2024-09-02 14:55:59"

    def test_exists(self, fake_temp_envs):
        env_0 = fake_temp_envs["env_0"]
        assert env_0.exists is False
        assert env_0.parent_exists is True  # sys.executable should exist!
        assert env_0.is_valid is False

        # Check the logic requires both exists and parent_exists to be True
        with mock.patch.object(
            TemporaryEnvironment,
            "exists",
            new_callable=mock.PropertyMock
        ) as mock_exists:
            mock_exists.return_value = True
            assert env_0.is_valid is True

            with mock.patch.object(
                TemporaryEnvironment,
                "parent_exists",
                new_callable=mock.PropertyMock
            ) as mock_parent_exists:
                mock_parent_exists.return_value = False
                assert env_0.is_valid is False


class TestAppEnv:
    def test_version_spec(self, fake_app_env):
        assert fake_app_env.version_spec == Version("0.1.0")

        assert not fake_app_env.is_outdated("v0.1.0")
        assert not fake_app_env.is_outdated("0.1.0")
        assert not fake_app_env.is_outdated("0.0.99")
        assert not fake_app_env.is_outdated("0.1.0rc3")

        assert fake_app_env.is_outdated("v0.1.1")
        assert fake_app_env.is_outdated("v0.1.1a1")


# CATALOGUE TESTS
def test_base_catalogue_noinit():
    # Base catalogue should not be created
    with pytest.raises(RuntimeError):
        _ = BaseCatalogue(path="cant/create/basecatalogue")

class TestTempCatalogue:
    # Shared tests for any catalogue
    def test_delete_env(self, fake_temp_catalogue, fake_temp_envs):
        with mock.patch("shutil.rmtree") as rmtree:
            pth = fake_temp_envs["env_0"].path

            fake_temp_catalogue.delete_env("env_0")

            rmtree.assert_called_once_with(pth)

            assert "env_0" not in fake_temp_catalogue.environments

    def test_delete_nonexistent_env(self, fake_temp_catalogue):
        with mock.patch("shutil.rmtree"):
            with pytest.raises(FileNotFoundError):
                fake_temp_catalogue.delete_env("env_42")

    def test_purge_folder(self, fake_temp_catalogue):
        with mock.patch("shutil.rmtree") as rmtree:
            fake_temp_catalogue.purge_folder()
            rmtree.assert_called_once_with(fake_temp_catalogue.catalogue_folder)

        assert fake_temp_catalogue.environments == {}

    def test_find_env_hash(self, fake_temp_catalogue, fake_temp_envs):
        example_paths = Path(__file__).parent / "example_scripts"

        # The python path and folder doesn't actually exist
        # But pretend it does
        with mock.patch.object(TemporaryEnvironment, "is_valid", new=True):
            env_0_spec = EnvironmentSpec.from_script(
                str(example_paths / "pep_723_example.py")
            )
            env_0_recover = fake_temp_catalogue.find_env_hash(spec=env_0_spec)

            # This should find the env without the lockfile
            env_1_and_2_spec = EnvironmentSpec.from_script(
                str(example_paths / "cowsay_ex_nolock.py")
            )
            env_2_recover = fake_temp_catalogue.find_env_hash(spec=env_1_and_2_spec)

            # This should only find the env *with* the lockfile
            # Despite being the same original spec
            env_3_spec = EnvironmentSpec.from_script(
                str(example_paths / "cowsay_ex.py")
            )
            env_3_recover = fake_temp_catalogue.find_env_hash(spec=env_3_spec)

        # env_1 should not be recovered even though it matches the spec
        # As it is marked as incomplete
        assert env_0_recover == fake_temp_envs["env_0"]
        assert env_2_recover == fake_temp_envs["env_2"]
        assert env_3_recover == fake_temp_envs["env_3"]

    def test_find_env_hash_fail(self, fake_full_catalogue):
        with (
            mock.patch.object(TemporaryCatalogue, "delete_env") as mock_delete,
            mock.patch.object(TemporaryEnvironment, "is_valid", new=False)
        ):
            example_paths = Path(__file__).parent / "example_scripts"
            env_0_spec = EnvironmentSpec.from_script(
                str(example_paths / "pep_723_example.py")
            )

            empty_recover = fake_full_catalogue.find_env_hash(spec=env_0_spec)

            assert empty_recover is None

            mock_delete.assert_called_with("env_0")

    def test_find_env_sufficient(self, fake_full_catalogue, fake_temp_envs):
        example_paths = Path(__file__).parent / "example_scripts"
        spec = EnvironmentSpec.from_script(
            example_paths / "pep_723_example_subset.py"
        )

        with mock.patch.object(TemporaryEnvironment, "is_valid", new=True):
            env_0_recover = fake_full_catalogue.find_sufficient_env(spec=spec)

        original_env = fake_temp_envs["env_0"]
        
        # env_0 has been updated
        assert env_0_recover.name == original_env.name
        assert env_0_recover.last_used_date > original_env.last_used_date

        # New spec has been added to the hashes
        assert env_0_recover.spec_hashes == [*original_env.spec_hashes, spec.spec_hash]

    def test_correct_find_env_called(self, fake_full_catalogue, fake_temp_envs):
        with (
            mock.patch.object(TemporaryEnvironment, "is_valid", new=True),
            mock.patch.object(
                TemporaryCatalogue, 
                "find_locked_env",
                wraps=fake_full_catalogue.find_locked_env,
            ) as mock_locked,
            mock.patch.object(
                TemporaryCatalogue, 
                "find_sufficient_env",
                wraps=fake_full_catalogue.find_sufficient_env,
            ) as mock_sufficient,
        ):
            example_paths = Path(__file__).parent / "example_scripts"
            
            # env_0 does not have a lock file, should look for sufficient
            env_0_spec = EnvironmentSpec.from_script(
                str(example_paths / "pep_723_example.py")
            )
            env_0_recover = fake_full_catalogue.find_env(spec=env_0_spec)
            assert fake_temp_envs["env_0"].name == env_0_recover.name
            mock_sufficient.assert_called_once_with(spec=env_0_spec)
            mock_locked.assert_not_called()
            mock_sufficient.reset_mock()
            mock_locked.reset_mock()

            # env_3 has a lockfile, should look for the matching lock env
            env_3_spec = EnvironmentSpec.from_script(
                str(example_paths / "cowsay_ex.py")
            )
            env_3_recover = fake_full_catalogue.find_env(spec=env_3_spec)
            assert fake_temp_envs["env_3"].name == env_3_recover.name
            mock_sufficient.assert_not_called()
            mock_locked.assert_called_once_with(spec=env_3_spec)
            mock_sufficient.reset_mock()
            mock_locked.reset_mock()

    # Temp catalogue specific tests
    def test_oldest_cache(self, fake_full_catalogue):
        assert fake_full_catalogue.oldest_cache == "env_0"

        # "Use" env_0
        env_0 = fake_full_catalogue.environments["env_0"]
        env_0.last_used = datetime.now().isoformat()

        with fake_full_catalogue.connection as con:
            env_0.update_row(con, columns=["last_used"])

        assert fake_full_catalogue.oldest_cache == "env_1"

        fake_full_catalogue.purge_folder()

        assert fake_full_catalogue.oldest_cache is None

    def test_expire_caches(self, fake_full_catalogue):
        with mock.patch.object(fake_full_catalogue, "delete_env") as del_env:
            # Expire all caches
            fake_full_catalogue.expire_caches(timedelta(seconds=1))

            calls = [
                mock.call("env_0"),
                mock.call("env_1"),
                mock.call("env_2"),
                mock.call("env_3"),
            ]

            assert del_env.mock_calls == calls
