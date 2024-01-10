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

from ducktools.lazyimporter import LazyImporter, ModuleImport

from ..shared import PythonInstall

_laz = LazyImporter([ModuleImport("re")])

PYTHON_VER_RE = r"\d{1,2}\.\d{1,2}\.\d+"
PYPY_VER_RE = r"^pypy(?P<pyversion>\d{1,2}\.\d+)-(?P<pypyversion>[\d\.]*)$"


PYENV_VERSIONS_FOLDER = os.path.expanduser(os.path.join("~", ".pyenv", "versions"))


def get_pyenv_pythons(
    versions_folder: str | os.PathLike = PYENV_VERSIONS_FOLDER,
) -> list[PythonInstall]:

    if not os.path.exists(versions_folder):
        return []

    python_versions = []
    for p in os.scandir(versions_folder):
        executable = os.path.join(p.path, "bin/python")

        if os.path.exists(executable):
            if _laz.re.fullmatch(PYTHON_VER_RE, p.name):
                python_versions.append(PythonInstall.from_str(p.name, executable))
            elif vermatches := _laz.re.fullmatch(PYPY_VER_RE, p.name):
                py_ver = vermatches.group("pyversion")
                pypy_ver = vermatches.group("pypyversion")
                python_versions.append(
                    PythonInstall.from_str(
                        version=py_ver,
                        executable=executable,
                        implementation="pypy",
                        metadata={"pypy_version": pypy_ver}
                    )
                )

    python_versions.sort(key=lambda x: x.version, reverse=True)

    return python_versions
