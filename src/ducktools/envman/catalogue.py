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

from ducktools.lazyimporter import LazyImporter, ModuleImport, FromImport, MultiFromImport

from prefab_classes import prefab, attribute
import prefab_classes.funcs as prefab_funcs

from .inline_dependencies import EnvironmentSpec


_laz = LazyImporter(
    [
        FromImport("datetime", "datetime"),
        ModuleImport("shutil"),
        ModuleImport("json"),
    ]
)

_packaging = LazyImporter(
    [
        MultiFromImport(
            "packaging.requirements",
            ["Requirement", "InvalidRequirement"],
        ),
        MultiFromImport(
            "packaging.specifiers",
            ["SpecifierSet", "InvalidSpecifier"],
        ),
        MultiFromImport(
            "packaging.version",
            ["Version", "InvalidVersion"]
        ),
    ]
)


def _datetime_now_iso():
    return _laz.datetime.now().isoformat()


@prefab
class CacheFolder:
    cache_name: str
    cache_path: str
    raw_specs: list[str]
    python_version: str
    installed_modules: list[str]
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
class CacheInfo:
    caches: dict[str, CacheFolder]

    def delete_cache(self, cachename):
        if cache := self.caches.get(cachename):
            cache.delete()
            del self.caches[cachename]
        else:
            raise FileNotFoundError(f"Cache {cachename!r} not found")

    def to_json(self) -> str:
        """Serialize this class into a JSON string"""
        # For external users that may not import prefab directly
        return prefab_funcs.to_json(self)

    @classmethod
    def from_json(cls, json_data) -> "CacheInfo":
        raw_data = _laz.json.loads(json_data)
        caches = {}
        for name, cache_info in raw_data.get("caches", {}):
            caches[name] = CacheFolder(**cache_info)
        return cls(caches=caches)  # noqa

    def strict_find_environment(self, spec: EnvironmentSpec) -> CacheFolder | None:
        """
        Attempt to find a cached python environment that matches the literal text
        of the specification.

        :param spec: EnvironmentSpec of requirements
        :return: CacheFolder details of python env that satisfies it or None
        """
        for cache in self.caches.values():
            if spec.raw_spec in cache.raw_specs:
                cache.last_used = _datetime_now_iso()
                return cache
        else:
            return None

    def loose_find_environment(self, spec: EnvironmentSpec) -> CacheFolder | None:
        """
        Check for a cache that matches the minimums of all specified modules

        If found, add the text of the spec to raw_specs for that module and return it

        :param spec: EnvironmentSpec requirements for a python environment
        :return: CacheFolder python environment details or None
        """
        for cache in self.caches.values():
            cache_pyver = _packaging.Version(cache.python_version)

            # Skip dependency check if python version does not match
            if cache_pyver not in spec.requires_python_spec:
                continue

            # Check dependencies
            cache_spec = {}

            for mod in cache.installed_modules:
                name, version = mod.split("==")
                # There should only be one specifier, specifying one version
                module_ver = _packaging.Version(version)
                cache_spec[name] = module_ver

            for req in spec.dependencies_spec:
                # If a dependency is not satisfied , break out of this loop
                if ver := cache_spec.get(req.name):
                    if ver not in req.specifier:
                        break
                else:
                    break
            else:
                # If all dependencies were satisfied, the loop completed
                # Update last_used and append this spec to raw_specs
                cache.last_used = _datetime_now_iso()
                cache.raw_specs.append(spec.raw_spec)
                return cache

        else:
            return None

    def find_environment(self, spec: EnvironmentSpec) -> CacheFolder | None:
        """
        Try to find an existing cached environment that satisfies the spec

        :param spec:
        :return:
        """
        if env := self.strict_find_environment(spec):
            return env
        return self.loose_find_environment(spec)

    def create_environment(self, spec: EnvironmentSpec) -> CacheFolder:
        ...
