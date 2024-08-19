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

import os.path

from ducktools.lazyimporter import LazyImporter, FromImport, ModuleImport, MultiFromImport

from . import PROJECT_NAME
from .config import Config, log
from .platform_paths import ManagedPaths
from .catalogue import TempCatalogue
from .environment_specs import EnvironmentSpec


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
        FromImport(".scripts.get_pip", "retrieve_pip")
    ],
    globs=globals(),
)


class Manager:
    project_name: str
    paths: ManagedPaths
    config: Config

    def __init__(self, project_name=PROJECT_NAME):
        self.project_name = project_name

        self.paths = ManagedPaths(PROJECT_NAME)
        self.config = Config.load(self.paths.config_path)
        self._temp_catalogue = None

    def __repr__(self):
        return f"{type(self).__name__}(project_name={self.project_name!r})"

    @property
    def temp_catalogue(self):
        if self._temp_catalogue is None:
            self._temp_catalogue = TempCatalogue.load(self.paths.cache_db)
        return self._temp_catalogue

    @property
    def is_installed(self):
        return os.path.exists(self.paths.pip_zipapp) and os.path.exists(self.paths.env_folder)

    # Ducktools build commands
    def retrieve_pip(self):
        return _laz.retrieve_pip(paths=self.paths)

    def build_env_folder(self, clear_old_builds=True) -> None:
        _laz.build_env_folder(paths=self.paths, clear_old_builds=clear_old_builds)

    def build_zipapp(self, clear_old_builds=True) -> None:
        """Build the ducktools.pyz zipapp"""
        _laz.build_zipapp(paths=self.paths, clear_old_builds=clear_old_builds)

    # Install and cleanup commands
    def install(self):
        # Install the ducktools package
        self.retrieve_pip()
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
    def get_script_env(self, path):
        spec = EnvironmentSpec.from_script(path)
        env = self.temp_catalogue.find_or_create_env(
            spec=spec, config=self.config, pip_zipapp=self.retrieve_pip()
        )
        return env

    def run_script(self, script_file, args) -> None:
        """Execute the provided script file with the given arguments"""
        env = self.get_script_env(script_file)
        log(f"Using environment at: {env.path}")
        _laz.subprocess.run([env.python_path, script_file, *args])

    def create_bundle(self, script_file: str) -> None:
        """Create a zipapp bundle for the provided script file"""
        if not self.is_installed:
            self.install()
        _laz.create_bundle(script_file, paths=self.paths)
