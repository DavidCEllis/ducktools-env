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

import os.path

from ducktools.lazyimporter import LazyImporter, ModuleImport, FromImport

from prefab_classes import prefab, attribute
from prefab_classes.funcs import to_json


_laz = LazyImporter(
    [
        FromImport("datetime", "datetime"),
        ModuleImport("shutil"),
    ]
)


def _datetime_now_iso():
    return _laz.datetime.now().isoformat()


@prefab
class CacheInfo:
    cache_name: str
    cache_path: str
    raw_specs: list[str]
    installed_modules: list[str]
    python_version: tuple[int, int, int]
    usage_count: int = 0
    created_on: str = attribute(default_factory=_datetime_now_iso)
    last_used: str = attribute(default_factory=_datetime_now_iso)

    @property
    def created_date(self):
        return _laz.datetime.fromisoformat(self.created_on)

    @property
    def last_used_date(self):
        return _laz.datetime.fromisoformat(self.last_used)

    @property
    def exists(self) -> bool:
        return os.path.exists(self.cache_path)

    def delete(self) -> None:
        """Delete the cache folder"""
        _laz.shutil.rmtree(self.cache_path)


@prefab
class MultiCache:
    caches: dict[str, CacheInfo]

    def delete_cache(self, cachename):
        if cache := self.caches.get(cachename):
            cache.delete()
            del self.caches[cachename]
        else:
            raise FileNotFoundError(f"Cache {cachename!r} not found")