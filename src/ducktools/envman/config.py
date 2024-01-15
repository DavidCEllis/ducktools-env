# DuckTools-EnvMan
# Copyright (C) 2024 David C Ellis
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Lesser General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Lesser General Public License for more details.
#
# You should have received a copy of the GNU Lesser General Public License
# along with this program.  If not, see <https://www.gnu.org/licenses/>.

import sys
import os
import os.path

from prefab_classes import prefab

from .exceptions import UnsupportedPlatformError

PROJECT_NAME = "ducktools"
CACHE_FOLDER_NAME = "venv_cache"

match sys.platform:
    case "win32":
        # os.path.expandvars will actually import a whole bunch of other modules
        # Try just using the environment.
        _local_app_folder = os.environ.get("LOCALAPPDATA")
        if not (_local_app_folder and os.path.isdir(_local_app_folder)):
            raise FileNotFoundError(f"Could not find local app data folder: {_local_app_folder!r}")
        BASE_FOLDER = os.path.join(_local_app_folder, PROJECT_NAME)
    case "linux":
        BASE_FOLDER = os.path.expanduser(os.path.join("~", f".{PROJECT_NAME}"))
    case "darwin":
        BASE_FOLDER = os.path.expanduser(
            os.path.join("~", "Library", "Caches", PROJECT_NAME)
        )
    case other:
        raise UnsupportedPlatformError(
            f"Platform {other!r} is not currently supported."
        )

CACHE_FOLDER = os.path.join(BASE_FOLDER, CACHE_FOLDER_NAME)


@prefab
class Config:
    cache_folder: str = CACHE_FOLDER
    cache_maxsize: int = 15
    cache_refresh: int = 30
