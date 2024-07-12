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

from ducktools.classbuilder.prefab import Prefab, attribute

from .platform_paths import get_platform_folder, get_platform_python

DEFAULT_PROJECT_NAME = "ducktools"

# Each OS has a different place where you would expect to keep application data
# Try to correctly use them
PLATFORM_FOLDER = get_platform_folder(DEFAULT_PROJECT_NAME)

# Folder for the manager environment
CORE_FOLDERNAME = "core"

# Filenames for configuration and catalogue
CONFIG_FILENAME = "config.json"
CATALOGUE_FILENAME = "catalogue.json"


class Config(Prefab):
    project_name: str = DEFAULT_PROJECT_NAME

    _project_folder: str | None = attribute(default=None, private=True)
    _core_python: str | None = attribute(default=None, private=True)

    @property
    def project_folder(self):
        if self._project_folder is None:
            folder_base = os.path.join(self.project_name, "environments")
            self._project_folder = get_platform_folder(folder_base)
        return self._project_folder

    @property
    def config_path(self):
        return os.path.join(self.project_folder, CONFIG_FILENAME)

    @property
    def core_folder(self):
        return os.path.join(self.project_folder, "core")

    @property
    def core_python(self):
        if self._core_python is None:
            self._core_python = get_platform_python(os.path.join(self.core_folder, "env"))
        return self._core_python
