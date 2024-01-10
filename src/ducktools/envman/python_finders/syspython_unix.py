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
Attempt to find python installs in the /usr/bin folder on *nix based systems
"""
import os.path

from ducktools.lazyimporter import LazyImporter, FromImport, MultiFromImport

from .shared import PythonInstall

_glob = LazyImporter([FromImport("glob", "glob")])

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

_platform = LazyImporter([FromImport("platform", "architecture")])

BIN_FOLDER = "/usr/bin"


class _LazyPythonRegexes:
    def __init__(self):
        self._is_potential_python = None
        self._python_v_re = None

    @property
    def is_potential_python(self):
        if not self._is_potential_python:
            self._is_potential_python = _re.compile(r"^python\d?\.?\d*$")
        return self._is_potential_python

    @property
    def python_v_re(self):
        # Python version from subprocess output
        if not self._python_v_re:
            self._python_v_re = _re.compile(r"^Python\s+(\d+.\d+.\d+)$")
        return self._python_v_re


REGEXES = _LazyPythonRegexes()


def get_system_python_installs(base_folder=BIN_FOLDER):
    installs = []
    potential_py = _glob.glob(os.path.join(base_folder, "python*"))
    for executable_path in potential_py:
        basename = os.path.relpath(executable_path, base_folder)
        if _re.fullmatch(REGEXES.is_potential_python, basename):
            version_output = (
                _subprocess.run([executable_path, "-V"], capture_output=True)
                .stdout.decode("utf-8")
                .strip()
            )

            version_match = _re.match(REGEXES.python_v_re, version_output)
            if version_match:
                version_txt = version_match.group(1)
                installs.append(
                    PythonInstall.from_str(
                        version=version_txt,
                        executable=executable_path,
                        architecture=_platform.architecture()[0],
                    )
                )

    return sorted(installs, key=lambda x: x.version, reverse=True)
