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

"""
Discover python installs that have been created with pyenv or pyenv-win
"""

import os
import os.path
import sys

from .shared import PythonVersion
from ..exceptions import ManagerNotFoundError


def get_pyenv_versions() -> list[PythonVersion]:

    if sys.platform == "win32":
        versions_folder = os.path.expanduser(os.path.join("~", ".pyenv", "pyenv-win", "versions"))
    else:
        versions_folder = os.path.expanduser(os.path.join("~", ".pyenv", "versions"))

    if not os.path.exists(versions_folder):
        ManagerNotFoundError("pyenv 'versions' folder not found")

    python_versions = []
    for p in os.scandir(versions_folder):
        executable = os.path.join(p.path, "python.exe" if sys.platform == "win32" else "bin/python")
        if os.path.exists(executable):
            python_versions.append(PythonVersion.from_str(p.name, executable))

    python_versions.sort(key=lambda x: x.version)

    return python_versions
