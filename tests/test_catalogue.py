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
import unittest.mock as mock
from datetime import datetime, timedelta
from pathlib import Path

from ducktools.classbuilder.prefab import as_dict

import pytest
from packaging.version import Version

from ducktools.env.catalogue import (
    BaseCatalogue, 
    ApplicationCatalogue,
    TempCatalogue, 
    ApplicationEnv,
    TemporaryEnv,
)

from ducktools.env.config import Config
from ducktools.env.environment_specs import EnvironmentSpec
from ducktools.env.exceptions import PythonVersionNotFound


@pytest.fixture
def mock_save():
    # Mock the .save() function from BaseCatalogue
    with mock.patch.object(BaseCatalogue, "save") as save_func:
        yield save_func


@pytest.fixture(scope="function")
def fake_temp_envs(catalogue_path):
    env_0_path = str(Path(catalogue_path).parent / "env_0")
    env_1_path = str(Path(catalogue_path).parent / "env_1")
    env_2_path = str(Path(catalogue_path).parent / "env_2")
    python_path = sys.executable
    python_version = ".".join(str(item) for item in sys.version_info[:3])

    # ENV examples based on examples folder
    env_0 = TemporaryEnv(
        name="env_0",
        path=env_0_path,
        python_version=python_version,
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
        python_version=python_version,
        parent_python=python_path,
        created_on="2024-09-02T14:55:58.827666",
        last_used="2024-09-02T14:55:58.827666",
        spec_hashes=["85cdf5c0f9b109ba70cd936b153fd175307406eb802e05df453d5ccf5a19383f"],
        installed_modules=["cowsay==6.1"],
    )

    env_2 = TemporaryEnv(
        name="env_2",
        path=env_2_path,
        python_version=python_version,
        parent_python=python_path,
        created_on="2024-09-25T17:55:23.254577",
        last_used="2024-09-26T11:29:12.233691",
        spec_hashes=["85cdf5c0f9b109ba70cd936b153fd175307406eb802e05df453d5ccf5a19383f"],
        lock_hash="840760dd5d911f145b94c72e670754391bf19c33d5272da7362b629c484fd1f6",
        installed_modules=["cowsay==6.1"],
    )

    return {"env_0": env_0, "env_1": env_1, "env_2": env_2}

@pytest.fixture
def fake_app_env(catalogue_path):
    python_path = sys.executable
    python_version = ".".join(str(item) for item in sys.version_info[:3])

    # Env based on examples folder
    appname = "ducktools_testing/cowsay_example"
    env = ApplicationEnv(
        name=appname,
        path=str(Path(catalogue_path).parent / "ducktools_testing/cowsay_example/env"),
        python_version=python_version,
        parent_python=python_path,
        created_on="2024-09-25T17:55:23.254577",
        last_used="2024-09-26T11:29:12.233691",
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
    

@pytest.fixture(scope="function")
def fake_temp_catalogue(catalogue_path, fake_temp_envs):
    cat = TempCatalogue(
        path=catalogue_path,
        environments=fake_temp_envs,
        env_counter=2,
    )

    yield cat


# ENVIRONMENT TESTS

@pytest.mark.usefixtures("mock_save")
class TestTempEnv:
    @pytest.mark.parametrize("envname", ["env_0", "env_1", "env_2"])
    def test_python_path(self, fake_temp_envs, envname, catalogue_path):
        env = fake_temp_envs[envname]
        base_path = Path(catalogue_path).parent

        if sys.platform == "win32":
            assert env.python_path == str(base_path / envname / "Scripts" / "python.exe")
        else:
            assert env.python_path == str(base_path / envname / "bin" / "python")
        
    @pytest.mark.skipif(sys.platform != "win32", reason="Windows only test")
    @pytest.mark.parametrize("envname", ["env_0", "env_1", "env_2"])
    def test_python_path_windowed(self, fake_temp_envs, envname, catalogue_path):
        # If there is no stdout on windows assume windowed executable
        with mock.patch("sys.stdout", new=None):
            env = fake_temp_envs[envname]
            base_path = Path(catalogue_path).parent

            assert env.python_path == str(base_path / envname / "Scripts" / "pythonw.exe")

    def test_dates(self, fake_temp_envs):
        env_0 = fake_temp_envs["env_0"]
        assert env_0.last_used_simple == "2024-09-02 14:55:53"

        env_1 = fake_temp_envs["env_1"]
        assert env_1.last_used_simple == "2024-09-02 14:55:58"
        
    def test_exists(self, fake_temp_envs):
        env_0 = fake_temp_envs["env_0"]
        assert env_0.exists is False
        assert env_0.parent_exists is True  # sys.executable should exist!
        assert env_0.is_valid is False

        # Check the logic requires both exists and parent_exists to be True
        with mock.patch.object(
            TemporaryEnv, 
            "exists", 
            new_callable=mock.PropertyMock
        ) as mock_exists:
            mock_exists.return_value = True
            assert env_0.is_valid is True

            with mock.patch.object(
                TemporaryEnv, 
                "parent_exists", 
                new_callable=mock.PropertyMock
            ) as mock_parent_exists:
                mock_parent_exists.return_value = False
                assert env_0.is_valid is False

    @pytest.mark.parametrize("envname", ["env_0", "env_1", "env_2"])
    def test_delete(self, fake_temp_envs, envname):
        with mock.patch("shutil.rmtree") as rmtree:
            env = fake_temp_envs[envname]
            env.delete()

            rmtree.assert_called_once_with(env.path)


@pytest.mark.usefixtures("mock_save")
class TestAppEnv:
    def test_version_spec(self, fake_app_env):
        assert fake_app_env.version_spec == Version("0.1.0")

        assert not fake_app_env.is_outdated("v0.1.0")
        assert not fake_app_env.is_outdated("0.1.0")
        assert not fake_app_env.is_outdated("0.0.99")
        assert not fake_app_env.is_outdated("0.1.0rc3")

        assert fake_app_env.is_outdated("v0.1.1")
        assert fake_app_env.is_outdated("v0.1.1a1")

    def test_delete(self, fake_app_env):
        with mock.patch("shutil.rmtree") as rmtree:
            fake_app_env.delete()

            del_path = str(Path(fake_app_env.path).parent)
            rmtree.assert_called_once_with(del_path)


# CATALOGUE TESTS

# All other tests mock out the save command
def test_catalogue_save(fake_temp_catalogue):
    cat = fake_temp_catalogue
    with (
        mock.patch("os.makedirs") as makedirs_mock,
        mock.patch("json.dump") as dump_mock,
        mock.patch("builtins.open") as open_mock
    ):
        file_mock = mock.MagicMock()
        open_mock.return_value.__enter__.return_value = file_mock

        cat.save()

        makedirs_mock.assert_called_once_with(cat.catalogue_folder, exist_ok=True)
        open_mock.assert_called_once_with(cat.path, "w")
        dump_mock.assert_called_once_with(cat, file_mock, default=as_dict, indent=2)

# Get python install has so many branches I wanted a separate test

class TestGetPythonInstall:
    example_paths = Path(__file__).parent / "example_scripts"

    def test_finds_python(self, fake_temp_catalogue):
        script = str(self.example_paths / "pep_723_example.py")
        spec = EnvironmentSpec.from_script(script)

        # Patch the spec version to match this python install
        this_python = ".".join(str(i) for i in sys.version_info[:3])
        spec.details.requires_python = f"=={this_python}"

        inst = fake_temp_catalogue._get_python_install(
            spec=spec,
            uv_path=None,
            config=Config(uv_install_python=False)
        )

        assert inst.executable == sys.executable

    
    def test_no_python(self, fake_temp_catalogue):
        script = str(self.example_paths / "pep_723_example.py")
        spec = EnvironmentSpec.from_script(script)

        # Patch the spec version to match this python install
        this_python = ".".join(str(i) for i in sys.version_info[:3])
        spec.details.requires_python = f">{this_python}"

        with pytest.raises(PythonVersionNotFound):
            fake_temp_catalogue._get_python_install(
                spec=spec,
                uv_path=None,
                config=Config(uv_install_python=False)
            )



@pytest.mark.usefixtures("mock_save")
class TestTempCatalogue:
    # Shared tests for any catalogue
    def test_load_env(self, fake_temp_catalogue):
        with (
            mock.patch("json.load") as mock_load,
            mock.patch("builtins.open") as mock_open,
        ):
            mock_file = mock.MagicMock()
            mock_open.return_value.__enter__.return_value = mock_file

            catalogue_dict = as_dict(fake_temp_catalogue)
            catalogue_dict["environments"] = {
                env.name: as_dict(env) 
                for env in catalogue_dict["environments"].values()
            }

            mock_load.return_value = catalogue_dict

            fake_path = "path/to/catalogue.json"

            cat = TempCatalogue.load(fake_path)

            assert cat == fake_temp_catalogue

            mock_open.assert_called_once_with(fake_path, 'r')
            mock_load.assert_called_once_with(mock_file)

    def test_load_fail_notfound(self):
        with mock.patch("builtins.open") as mock_open:
            mock_open.side_effect = FileNotFoundError()
            fake_path = "path/to/catalogue.json"

            cat = TempCatalogue.load(fake_path)

            assert cat == TempCatalogue(path=fake_path)

    def test_delete_env(self, fake_temp_catalogue, fake_temp_envs, mock_save):
        with mock.patch("shutil.rmtree") as rmtree:
            pth = fake_temp_envs["env_0"].path

            fake_temp_catalogue.delete_env("env_0")

            rmtree.assert_called_once_with(pth)

            mock_save.assert_called()

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
        with mock.patch.object(TemporaryEnv, "is_valid", new=True):
            env_0_spec = EnvironmentSpec.from_script(
                str(example_paths / "pep_723_example.py")
            )
            env_0_recover = fake_temp_catalogue.find_env_hash(spec=env_0_spec)

            # This should find the env without the lockfile
            env_1_spec = EnvironmentSpec.from_script(
                str(example_paths / "cowsay_ex_nolock.py")
            )
            env_1_recover = fake_temp_catalogue.find_env_hash(spec=env_1_spec)

            # This should only find the env *with* the lockfile
            # Despite being the same original spec
            env_2_spec = EnvironmentSpec.from_script(
                str(example_paths / "cowsay_ex.py")
            )
            env_2_recover = fake_temp_catalogue.find_env_hash(spec=env_2_spec)

        assert env_0_recover == fake_temp_envs["env_0"]
        assert env_1_recover == fake_temp_envs["env_1"]
        assert env_2_recover == fake_temp_envs["env_2"]

    def test_find_env_hash_fail(self, fake_temp_catalogue):
        with (
            mock.patch.object(TempCatalogue, "delete_env") as mock_delete,
            mock.patch.object(TemporaryEnv, "is_valid", new=False)
        ):
            example_paths = Path(__file__).parent / "example_scripts"
            env_0_spec = EnvironmentSpec.from_script(
                str(example_paths / "pep_723_example.py")
            )

            empty_recover = fake_temp_catalogue.find_env_hash(spec=env_0_spec)

            assert empty_recover is None

            mock_delete.assert_called_with("env_0")


    # Temp catalogue specific tests
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