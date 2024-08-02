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

from ducktools.lazyimporter import LazyImporter, MultiFromImport

from ._version import __version__
from .config import Config
from .platform_paths import default_paths, ManagedPaths
from .catalogue import TempCatalogue
from .environment_specs import SpecType, EnvironmentSpec

PROJECT_NAME = "ducktools"


_laz = LazyImporter(
    [
        MultiFromImport(
            "packaging.version",
            ["Version", "InvalidVersion"]
        )
    ]
)


class Manager:
    project_name: str
    paths: ManagedPaths
    config: Config

    def __init__(self, project_name=PROJECT_NAME):
        self.project_name = project_name

        self.paths = default_paths
        self.config = Config.load(self.paths.config_path)

        self._temp_catalogue = None

    def __repr__(self):
        return f"{type(self).__name__}(project_name={self.project_name!r})"

    @property
    def temp_catalogue(self):
        if self._temp_catalogue is None:
            self._temp_catalogue = TempCatalogue.load(self.paths.cache_db)
        return self._temp_catalogue

    def get_script_env(self, path):
        spec = EnvironmentSpec.from_script(path)
        env = self.temp_catalogue.find_or_create_env(spec=spec, config=self.config)
        return env

    def purge_cache(self):
        self.temp_catalogue.purge_folder()
