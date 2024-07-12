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
import os

from .exceptions import UnsupportedPlatformError

PROJECT_NAME = "ducktools"

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
    PLATFORM_FOLDER = os.path.join(_local_app_folder, PROJECT_NAME)
elif sys.platform == "linux":
    PLATFORM_FOLDER = os.path.expanduser(os.path.join("~", f".{PROJECT_NAME}"))
elif sys.platform == "darwin":
    raise UnsupportedPlatformError(
        f"MacOS is not yet supported."
    )
    # PLATFORM_FOLDER = os.path.expanduser(
    #     os.path.join("~", "Library", "Caches", PROJECT_NAME)
    # )
else:
    raise UnsupportedPlatformError(
        f"Platform {sys.platform!r} is not currently supported."
    )

# This is the base folder for all configuration and environments
BASE_PROJECT_FOLDERNAME = os.path.join(PLATFORM_FOLDER, "environments")

# Folder for the manager environment
CORE_FOLDERNAME = "core"
CORE_FOLDER = os.path.join(BASE_PROJECT_FOLDERNAME, CORE_FOLDERNAME)
CORE_VENV = os.path.join(CORE_FOLDER, "env")

# Python executable path for core python
if sys.platform == "win32":
    CORE_PYTHON = os.path.join(CORE_VENV, "Scripts", "python.exe")
else:
    CORE_PYTHON = os.path.join(CORE_VENV, "bin", "python")

# Filenames for configuration and catalogue
CONFIG_FILENAME = "config.json"
CATALOGUE_FILENAME = "catalogue.json"
