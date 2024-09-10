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
from __future__ import annotations

import sys
import os
import os.path

from ducktools.lazyimporter import LazyImporter, FromImport, ModuleImport, MultiFromImport
from ducktools.classbuilder.prefab import Prefab, attribute

from . import (
    FOLDER_ENVVAR,
    PROJECT_NAME,
    DATA_BUNDLE_ENVVAR,
    DATA_BUNDLE_FOLDER,
    LAUNCH_ENVIRONMENT_ENVVAR,
    LAUNCH_PATH_ENVVAR,
    LAUNCH_TYPE_ENVVAR,
)
from .config import Config, log
from .platform_paths import ManagedPaths
from .catalogue import TempCatalogue
from .environment_specs import EnvironmentSpec
from .exceptions import UVUnavailableError


_laz = LazyImporter(
    [
        # stdlib
        ModuleImport("shutil"),
        ModuleImport("subprocess"),
        # third party
        MultiFromImport(
            "packaging.version",
            ["Version", "InvalidVersion"]
        ),
        # internal
        FromImport(".bundle", "create_bundle"),
        MultiFromImport(
            ".scripts.create_zipapp",
            ["build_env_folder", "build_zipapp"]
        ),
        FromImport(".scripts.get_pip", "retrieve_pip"),
        FromImport(".scripts.get_uv", "retrieve_uv"),
    ],
    globs=globals(),
)


class Manager(Prefab):
    project_name: str = PROJECT_NAME
    config: Config = None

    paths: ManagedPaths = attribute(init=False, repr=False)
    _temp_catalogue: TempCatalogue | None = attribute(default=None, private=True)

    def __prefab_post_init__(self, config):
        self.paths = ManagedPaths(PROJECT_NAME)
        self.config = Config.load(self.paths.config_path) if config is None else config

    @property
    def temp_catalogue(self):
        if self._temp_catalogue is None:
            self._temp_catalogue = TempCatalogue.load(self.paths.cache_db)

            # Clear expired caches on load
            self._temp_catalogue.expire_caches(self.config.cache_lifetime_delta)
        return self._temp_catalogue

    @property
    def is_installed(self):
        return os.path.exists(self.paths.pip_zipapp) and os.path.exists(self.paths.env_folder)

    # Ducktools build commands
    def retrieve_pip(self) -> str:
        return _laz.retrieve_pip(paths=self.paths)

    def retrieve_uv(self, required=False) -> str | None:
        import inspect
        for f in inspect.stack():
            print(f.code_context)
        if self.config.use_uv or required:
            uv_path = _laz.retrieve_uv(paths=self.paths)
        else:
            uv_path = None

        if uv_path is None and required:
            raise UVUnavailableError(
                "UV is required for this process but is unavailable"
            )

        return uv_path

    @property
    def install_base_command(self) -> list[str]:
        # Get the installer command for python packages
        # Pip or the faster uv_pip if it is available
        if uv_path := self.retrieve_uv():
            return [uv_path, "pip"]
        else:
            pip_path = self.retrieve_pip()
            return [sys.executable, pip_path, "--disable-pip-version-check"]

    def build_env_folder(self, clear_old_builds=True) -> None:
        # build_env_folder will use PIP as uv will fail
        # if there is no environment
        # build-env-folder installs into a target directory
        # instead of using a venv
        base_command = [sys.executable, self.retrieve_pip(), "--disable-pip-version-check"]
        _laz.build_env_folder(
            paths=self.paths,
            install_base_command=base_command,
            clear_old_builds=clear_old_builds,
        )

    def build_zipapp(self, clear_old_builds=True) -> None:
        """Build the ducktools.pyz zipapp"""
        base_command = [sys.executable, self.retrieve_pip(), "--disable-pip-version-check"]
        _laz.build_zipapp(
            paths=self.paths,
            install_base_command=base_command,
            clear_old_builds=clear_old_builds,
        )

    # Install and cleanup commands
    def install(self):
        # Install the ducktools package
        self.build_env_folder(clear_old_builds=True)

    def clear_temporary_cache(self):
        # Clear the temporary environment cache
        log(f"Deleting temporary caches at {self.paths.cache_folder!r}")
        self.temp_catalogue.purge_folder()

    def clear_project_folder(self):
        # Clear the entire ducktools folder
        root_path = self.paths.project_folder
        log(f"Deleting full cache at {root_path!r}")
        _laz.shutil.rmtree(root_path, ignore_errors=True)

    # Script running and bundling commands
    def get_script_env(self, spec: EnvironmentSpec):
        env = self.temp_catalogue.find_env(spec=spec)

        if not env:
            log("Existing environment not found, creating new environment.")
            env = self.temp_catalogue.create_env(
                spec=spec,
                config=self.config,
                uv_path=self.retrieve_uv(),
                installer_command=self.install_base_command,
            )
        return env

    def run_bundled_script(
        self,
        *,
        spec: EnvironmentSpec,
        zipapp_path: str,
        args: list[str],
    ):
        env_vars = {
            LAUNCH_TYPE_ENVVAR: "BUNDLE",
            LAUNCH_PATH_ENVVAR: zipapp_path,
        }

        # If the spec indicates there should be data
        # include the bundle data folder in the archive
        if spec.details.data_sources:
            env_vars[DATA_BUNDLE_ENVVAR] = f"{DATA_BUNDLE_FOLDER}/"

        self.run_script(
            spec=spec,
            args=args,
            env_vars=env_vars,
        )

    def run_direct_script(
        self,
        *,
        spec: EnvironmentSpec,
        args: list[str],
    ):
        env_vars = {
            LAUNCH_TYPE_ENVVAR: "SCRIPT",
            LAUNCH_PATH_ENVVAR: spec.script_path,
        }

        # Add sources to env variable
        if sources := spec.details.data_sources:
            split_char = ";" if sys.platform == "win32" else ":"
            env_vars[DATA_BUNDLE_ENVVAR] = split_char.join(sources)

        self.run_script(
            spec=spec,
            args=args,
            env_vars=env_vars,
        )

    def run_script(
        self,
        *,
        spec: EnvironmentSpec,
        args: list[str],
        env_vars: dict[str, str] | None = None,
    ) -> None:
        """Execute the provided script file with the given arguments

        :param spec: EnvironmentSpec
        :param args: arguments to be provided to the script file
        :param env_vars: Environment variables to set
        """
        env = self.get_script_env(spec)
        env_vars[FOLDER_ENVVAR] = self.paths.project_folder
        env_vars[LAUNCH_ENVIRONMENT_ENVVAR] = env.path
        log(f"Using environment at: {env.path}")

        # Update environment variables for access from subprocess
        os.environ.update(env_vars)
        _laz.subprocess.run([env.python_path, spec.script_path, *args])

    def create_bundle(
        self,
        *,
        spec: EnvironmentSpec,
        output_file: str | None = None,
    ) -> None:
        """Create a zipapp bundle for the provided script file

        :param spec: EnvironmentSpec
        :param output_file: output path to zipapp bundle (script_file.pyz default)
        """
        if not self.is_installed:
            self.install()

        _laz.create_bundle(
            script_file=spec.script_path,
            output_file=output_file,
            paths=self.paths,
            installer_command=self.install_base_command,
            lockdata=spec.lockdata,
        )
