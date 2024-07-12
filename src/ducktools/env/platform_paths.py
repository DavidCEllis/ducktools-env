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


class UnsupportedPlatformError(Exception):
    pass


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
