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

# This is used as a bootstrapping script as well as internally
# For this reason it can't use any non-stdlib modules.

from __future__ import annotations

import sys
import os


class UnsupportedPlatformError(Exception):
    pass


ENVIRONMENTS_SUBFOLDER = "environments"

# Folders used internally
CACHEDENV_FOLDERNAME = "caches"
APPLICATION_FOLDERNAME = "application"
VENV_FOLDERNAME = "env"

MANAGER_FOLDERNAME = "lib"

# Filenames for configuration and catalogue
CONFIG_FILENAME = "config.json"
CATALOGUE_FILENAME = "catalogue.json"


# Each OS has a different place where you would expect to keep application data
# Try to correctly use them
if sys.platform == "win32":
    # os.path.expandvars will actually import a whole bunch of other modules
    # Try just using the environment.
    if _local_app_folder := os.environ.get("LOCALAPPDATA"):
        if not os.path.isdir(_local_app_folder):
            raise FileNotFoundError(
                f"Could not find local app data folder {_local_app_folder}"
            )
    else:
        raise EnvironmentError(
            "Environment variable %LOCALAPPDATA% "
            "for local application data folder location "
            "not found"
        )
    USER_FOLDER = _local_app_folder
elif sys.platform == "linux":
    USER_FOLDER = os.path.expanduser("~")
elif sys.platform == "darwin":
    raise UnsupportedPlatformError(
        f"MacOS is not yet supported."
    )
    # PLATFORM_FOLDER = os.path.expanduser(
    #     os.path.join("~", "Library", "Caches")
    # )
else:
    raise UnsupportedPlatformError(
        f"Platform {sys.platform!r} is not currently supported."
    )


def get_platform_python(venv_folder):
    if sys.platform == "win32":
        return os.path.join(venv_folder, "Scripts", "python.exe")
    else:
        return os.path.join(venv_folder, "bin", "python")


def get_platform_folder(name):
    if sys.platform == "linux":
        return os.path.join(USER_FOLDER, f".{name}")
    else:
        return os.path.join(USER_FOLDER, name)


class ManagedPaths:
    project_name: str
    project_folder: str
    config_path: str

    manager_folder: str
    pip_zipapp: str
    env_zipapp: str

    application_folder: str  # Not yet used
    cache_folder: str

    cache_db: str

    build_base: str

    def __init__(self, project_name="ducktools"):
        self.project_name = project_name

        folder_base = os.path.join(self.project_name, ENVIRONMENTS_SUBFOLDER)

        self.project_folder = get_platform_folder(folder_base)
        self.config_path = os.path.join(self.project_folder, CONFIG_FILENAME)

        self.manager_folder = os.path.join(self.project_folder, MANAGER_FOLDERNAME)
        self.pip_zipapp = os.path.join(self.manager_folder, "pip.pyz")
        self.env_zipapp = os.path.join(self.manager_folder, "ducktools.pyz")

        self.application_folder = os.path.join(self.project_folder, APPLICATION_FOLDERNAME)
        self.cache_folder = os.path.join(self.project_folder, CACHEDENV_FOLDERNAME)
        self.cache_db = os.path.join(self.cache_folder, CATALOGUE_FILENAME)

        self.build_base = os.path.join(self.project_folder, "build")

    @staticmethod
    def get_app_version(versionfile):
        minimal_version = (0, 0)
        if not os.path.exists(versionfile):
            return minimal_version
        with open(versionfile, 'r') as f:
            raw_version = f.read()
        try:
            ver = tuple(int(arg) for arg in raw_version.split("."))
        except ValueError:
            return minimal_version
        return ver

    def get_pip_version(self):
        version_file = f"{self.pip_zipapp}.version"
        return self.get_app_version(version_file)

    def get_env_version(self):
        version_file = f"{self.env_zipapp}.version"
        return self.get_app_version(version_file)

    def build_folder(self):
        """
        Get a temporary folder to use for builds
        """
        # Time to use slow stuff
        os.makedirs(self.build_base, exist_ok=True)

        import tempfile
        return tempfile.mkdtemp(dir=self.build_base)


default_paths = ManagedPaths()


if __name__ == "__main__":
    paths = default_paths
    print(paths.project_folder)
    print(paths.config_path)
    print(paths.cache_folder)
    print(paths.cache_db)


