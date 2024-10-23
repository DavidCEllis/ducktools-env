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
import sys
import os
import os.path


class UnsupportedPlatformError(Exception):
    pass


PACKAGE_SUBFOLDER = "env"

# Folders used internally
CACHEDENV_FOLDERNAME = "caches"
APPLICATION_FOLDERNAME = "applications"

MANAGER_FOLDERNAME = "lib"

# Filenames for configuration and catalogue
CONFIG_FILENAME = "config.json"
CATALOGUE_FILENAME = "catalogue.db"
APPCATALOGUE_FILENAME = "app_catalogue.db"

# Filename for the script register
REGISTER_FILENAME = "scripts.db"


# Store in LOCALAPPDATA for windows, User folder for other operating systems
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
else:
    USER_FOLDER = os.path.expanduser("~")


def get_platform_python(venv_folder):
    if sys.platform == "win32":
        if sys.stdout:
            return os.path.join(venv_folder, "Scripts", "python.exe")
        else:
            return os.path.join(venv_folder, "Scripts", "pythonw.exe")
    else:
        return os.path.join(venv_folder, "bin", "python")


def get_platform_folder(name):
    if sys.platform == "win32":
        return os.path.join(USER_FOLDER, name)
    else:
        return os.path.join(USER_FOLDER, f".{name}")


class ManagedPaths:
    project_name: str
    project_folder: str
    config_path: str

    manager_folder: str
    pip_zipapp: str
    uv_executable: str
    env_folder: str

    application_folder: str
    application_db: str

    cache_folder: str
    cache_db: str

    register_db: str

    build_base: str

    def __init__(self, project_name="ducktools"):
        self.project_name = project_name

        folder_base = os.path.join(self.project_name, PACKAGE_SUBFOLDER)

        self.project_folder = get_platform_folder(folder_base)
        self.config_path = os.path.join(self.project_folder, CONFIG_FILENAME)

        self.manager_folder = os.path.join(self.project_folder, MANAGER_FOLDERNAME)
        self.pip_zipapp = os.path.join(self.manager_folder, "pip.pyz")
        self.uv_executable = os.path.join(
            self.manager_folder,
            "uv.exe" if sys.platform == "win32" else "uv",
        )
        self.env_folder = os.path.join(self.manager_folder, "ducktools-env")

        self.application_folder = os.path.join(self.project_folder, APPLICATION_FOLDERNAME)
        self.application_db = os.path.join(self.application_folder, APPCATALOGUE_FILENAME)

        self.cache_folder = os.path.join(self.project_folder, CACHEDENV_FOLDERNAME)
        self.cache_db = os.path.join(self.cache_folder, CATALOGUE_FILENAME)

        self.register_db = os.path.join(self.project_folder, REGISTER_FILENAME)

        self.build_base = os.path.join(self.project_folder, "build")

    @staticmethod
    def get_app_version(versionfile):
        try:
            with open(versionfile, 'r') as f:
                ver = f.read()
        except FileNotFoundError:
            return None
        return ver

    def get_pip_version(self):
        version_file = f"{self.pip_zipapp}.version"
        return self.get_app_version(version_file)

    def get_env_version(self):
        version_file = f"{self.env_folder}.version"
        return self.get_app_version(version_file)

    def get_uv_version(self):
        version_file = f"{self.uv_executable}.version"
        return self.get_app_version(version_file)

    def build_folder(self):
        """
        Get a temporary folder to use for builds
        """
        # Time to use slow stuff
        os.makedirs(self.build_base, exist_ok=True)

        import tempfile
        return tempfile.TemporaryDirectory(dir=self.build_base)
