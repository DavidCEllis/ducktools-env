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

from prefab_classes import prefab, attribute


@prefab
class PythonInstall:
    version: tuple[int, ...]
    executable: str
    architecture: str = "64bit"
    metadata: dict = attribute(default_factory=dict)

    @classmethod
    def from_str(
            cls,
            version: str,
            executable: str,
            architecture: str = "64bit",
            metadata: dict | None = None,
    ):
        version_tuple = tuple(int(val) for val in version.split("."))
        return cls(version_tuple, executable, architecture, metadata)  # noqa
