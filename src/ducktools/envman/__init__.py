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

from ducktools.lazyimporter import LazyImporter, FromImport, MultiFromImport, get_module_funcs

__all__ = [
    "__version__",  # noqa
    "Catalogue",  # noqa
    "CachedEnv",  # noqa
    "Config",  # noqa
]

_laz = LazyImporter(
    [
        FromImport(".version", "__version__"),
        MultiFromImport(".catalogue", ["Catalogue", "CachedEnv"]),
        FromImport(".config", "Config"),
    ],
    globs=globals(),
)

__getattr__, __dir__ = get_module_funcs(_laz)
