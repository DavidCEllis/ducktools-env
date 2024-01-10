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
Discover python installs using the windows 'py' launcher
"""

from ducktools.lazyimporter import LazyImporter, FromImport, MultiFromImport

from .shared import PythonVersion
from ..exceptions import ManagerNotFoundError


_subprocess = LazyImporter([FromImport("subprocess", "run")])

_re = LazyImporter(
    [
        MultiFromImport(
            "re",
            [
                "compile",
                "fullmatch",
                "match",
            ],
        )
    ]
)


class _LazyPythonRegexes:
    def __init__(self):
        self._py_versions_re = None
        self._python_v_re = None

    @property
    def py_versions_re(self):
        if not self._py_versions_re:
            self._py_versions_re = _re.compile(r"^.+V:(\d+.\d+)[\s|*]+(.+)$")
        return self._py_versions_re

    @property
    def python_v_re(self):
        if not self._python_v_re:
            self._python_v_re = _re.compile(r"^Python\s+(\d+.\d+.\d+)$")
        return self._python_v_re


def get_py_install_versions(precise=False) -> list[PythonVersion]:
    try:
        result = _subprocess.run(["py", "--list-paths"], capture_output=True)
    except FileNotFoundError:
        raise ManagerNotFoundError("py launcher not installed or present on PATH.")

    output = result.stdout.decode("UTF-8").split("\r\n")

    versions = []

    regexes = _LazyPythonRegexes()

    for line in output:
        data = _re.fullmatch(regexes.py_versions_re, line)
        if data:
            python_path = data.group(2)
            if precise:
                # Get exact version from `python.exe -V` output
                version_output = (
                    _subprocess.run([python_path, "-V"], capture_output=True)
                    .stdout.decode("utf-8")
                    .strip()
                )

                version_txt = _re.match(regexes.python_v_re, version_output).group(1)
            else:
                # The version 'py' gives is not the full python version
                # But is probably good enough
                version_txt = data.group(1)

            versions.append(PythonVersion.from_str(version_txt, python_path))

    versions.sort(reverse=True, key=lambda x: x.version)

    return versions
