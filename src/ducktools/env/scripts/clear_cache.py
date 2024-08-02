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

import shutil

from ducktools.env.platform_paths import default_paths


def clear_cache(paths=default_paths):
    root_path = default_paths.project_folder
    print(f"Deleting cache at {root_path!r}")
    shutil.rmtree(root_path, ignore_errors=True)


if __name__ == "__main__":
    clear_cache()
