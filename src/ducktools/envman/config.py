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
import datetime

from prefab_classes import prefab

from .exceptions import UnsupportedPlatformError

PROJECT_NAME = "ducktools"
CACHE_FOLDER_NAME = "venv_caches"
CACHE_FILENAME = f"cache_details.json"
CACHE_EXPIRY_DAYS = 30

match sys.platform:
    case "win32":
        # os.path.expandvars will actually import a whole bunch of other modules
        # Try just using the environment.
        if _local_app_folder := os.environ.get("LOCALAPPDATA"):
            if not os.path.isdir(_local_app_folder):
                raise FileNotFoundError(
                    f"Could not find local app data folder {_local_app_folder}"
                )
        else:
            raise EnvironmentError("Environment variable %LOCALAPPDATA% not found")
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
    """
    Configuration for the environment manager.

    :param cache_folder: string path to the cache folder
    :param cache_db_name: string path to the cache filename
    :param cache_maxsize: maximum number of environments to keep cached
    :param cache_expires: delete/restore a cache after it is this old
    """
    cache_folder: str = CACHE_FOLDER
    cache_db_name: str = CACHE_FILENAME
    cache_maxsize: int = 15
    cache_expires: datetime.timedelta | None = datetime.timedelta(days=CACHE_EXPIRY_DAYS)

    @property
    def cache_db_path(self):
        return os.path.join(self.cache_folder, self.cache_db_name)
