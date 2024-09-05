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
import os.path

from ducktools.lazyimporter import LazyImporter, FromImport, ModuleImport, MultiFromImport
from ducktools.classbuilder.prefab import Prefab, attribute

from . import PROJECT_NAME
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

    def retrieve_uv(self) -> str | None:
        if self.config.use_uv:
            return _laz.retrieve_uv(paths=self.paths)
        return None

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
        _laz.build_env_folder(
            paths=self.paths,
            install_base_command=self.install_base_command,
            clear_old_builds=clear_old_builds,
        )

    def build_zipapp(self, clear_old_builds=True) -> None:
        """Build the ducktools.pyz zipapp"""
        _laz.build_zipapp(
            paths=self.paths,
            install_base_command=self.install_base_command,
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
    def get_script_env(self, path: str, *, lockdata: str | None = None):
        spec = EnvironmentSpec.from_script(path, lockdata=lockdata)
        env = self.temp_catalogue.find_or_create_env(
            spec=spec,
            config=self.config,
            uv_path=self.retrieve_uv(),
            installer_command=self.install_base_command,
        )
        return env

    def create_lockfile(
        self, 
        script_file: str, 
        lockfile: str | None = None
    ) -> None:
        if uv_path := self.retrieve_uv():
            spec = EnvironmentSpec.from_script(script_file)
            lock_data = spec.generate_lockdata(uv_path=uv_path)
            if lockfile is None:
                lockfile = f"{script_file}.lock"

            log(f"Writing lockfile to {lockfile!r}")
            with open(lockfile, "w") as f:
                f.write(lock_data)
        else:
            raise UVUnavailableError("UV is required to generate lockfiles.")

    def run_script(
        self,
        *,
        script_file: str,
        args: list[str],
        lockdata: str | None = None,
    ) -> None:
        """Execute the provided script file with the given arguments

        :param script_file: path to the script file to run
        :param args: arguments to be provided to the script file
        :param lockfile: string lockfile data
        """
        env = self.get_script_env(script_file, lockdata=lockdata)
        log(f"Using environment at: {env.path}")
        _laz.subprocess.run([env.python_path, script_file, *args])

    def create_bundle(
        self,
        *,
        script_file: str,
        output_file: str | None = None,
        lockfile: str | None = None,
    ) -> None:
        """Create a zipapp bundle for the provided script file

        :param script_file: path to the script file to bundle
        :param output_file: output path to zipapp bundle (script_file.pyz default)
        :param lockfile: lockfile path if provided
        """
        if not self.is_installed:
            self.install()

        _laz.create_bundle(
            script_file=script_file,
            output_file=output_file,
            paths=self.paths,
            installer_command=self.install_base_command,
            lockfile=lockfile,
        )
