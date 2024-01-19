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
import os.path
from datetime import datetime as _datetime

from ducktools.lazyimporter import LazyImporter, FromImport, ModuleImport, MultiFromImport

from prefab_classes import prefab, attribute
import prefab_classes.funcs as prefab_funcs

from .inline_dependencies import EnvironmentSpec
from .config import Config
from .exceptions import PythonVersionNotFound, InvalidEnvironmentSpec, VenvBuildError


_laz = LazyImporter(
    [
        ModuleImport("shutil"),
        ModuleImport("json"),
        ModuleImport("subprocess"),
        FromImport("ducktools.pythonfinder", "get_python_installs"),
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


def _datetime_now_iso() -> str:
    """
    Helper function to allow use of datetime.now with iso formatting
    as a default factory
    """
    return _datetime.now().isoformat()


@prefab
class CachedEnv:
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
        return _datetime.fromisoformat(self.created_on)

    @property
    def last_used_date(self):
        return _datetime.fromisoformat(self.last_used)

    @property
    def exists(self) -> bool:
        return os.path.exists(self.cache_path)

    def delete(self) -> None:
        """Delete the cache folder"""
        _laz.shutil.rmtree(self.cache_path)


@prefab
class CacheInfo:
    caches: dict[str, CachedEnv]
    config: Config
    env_counter: int = 1

    def delete_cache(self, cachename):
        if cache := self.caches.get(cachename):
            cache.delete()
            del self.caches[cachename]
        else:
            raise FileNotFoundError(f"Cache {cachename!r} not found")

    def purge_cache_folder(self):
        """
        Clear the cache folder when things have gone wrong or for a new version.
        """
        try:
            _laz.shutil.rmtree(self.config.cache_folder)
        except FileNotFoundError:
            pass
        os.makedirs(self.config.cache_folder, exist_ok=False)

    @property
    def oldest_cache(self) -> str | None:
        """
        :return: name of the oldest cache or None if there are no caches
        """
        old_cache = None
        for cache in self.caches.values():
            if old_cache:
                if cache.last_used < old_cache.last_used:
                    old_cache = cache
            else:
                old_cache = cache

        if old_cache:
            return old_cache.cache_name
        else:
            return old_cache

    def expire_caches(self):
        if delta := self.config.cache_expires:
            ctime = _datetime.now()
            for cachename, cache in self.caches.items():
                if (ctime - cache.created_date) > delta:
                    self.delete_cache(cachename)

        self.save_cache()

    def save_cache(self) -> None:
        """Serialize this class into a JSON string and save"""
        # For external users that may not import prefab directly
        data = prefab_funcs.to_json(self, excludes=("config",), indent=2)

        os.makedirs(self.config.cache_folder, exist_ok=True)

        with open(self.config.cache_db_path, 'w') as f:
            f.write(data)

    @classmethod
    def from_config(cls, config: Config) -> "CacheInfo":
        try:
            with open(config.cache_db_path, 'r') as f:
                raw_caches = _laz.json.load(f)
        except FileNotFoundError:
            raw_caches = {}

        caches = {
            name: CachedEnv(**cache_info)
            for name, cache_info
            in raw_caches.get("caches", {}).items()
        }

        env_counter = raw_caches.get("env_counter", 1)

        # noinspection PyArgumentList
        return cls(
            caches=caches,
            env_counter=env_counter,
            config=config
        )

    def _strict_find_env(self, spec: EnvironmentSpec) -> CachedEnv | None:
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

    def _loose_find_env(self, spec: EnvironmentSpec) -> CachedEnv | None:
        """
        Check for a cache that matches the minimums of all specified modules

        If found, add the text of the spec to raw_specs for that module and return it

        :param spec: EnvironmentSpec requirements for a python environment
        :return: CacheFolder python environment details or None
        """
        for cache in self.caches.values():
            # If no python version listed ignore it
            # If python version is listed, make sure it matches
            if spec.requires_python:
                cache_pyver = _packaging.Version(cache.python_version)
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

    def find_env(self, spec: EnvironmentSpec) -> CachedEnv | None:
        """
        Try to find an existing cached environment that satisfies the spec

        :param spec:
        :return:
        """
        env = self._strict_find_env(spec) or self._loose_find_env(spec)

        if env:
            # Update the cache file
            self.save_cache()

        return env

    def create_env(self, spec: EnvironmentSpec) -> CachedEnv:
        # Check the spec is valid
        if spec_errors := spec.errors():
            raise InvalidEnvironmentSpec("; ".join(spec_errors))

        # Delete the oldest cache if there are too many
        if len(self.caches) >= self.config.cache_maxsize:
            self.delete_cache(self.oldest_cache)

        new_cachename = f"caches_{self.env_counter}"
        self.env_counter += 1
        cache_path = os.path.join(self.config.cache_folder, new_cachename)

        # Find a valid python executable
        for install in _laz.get_python_installs():
            if not spec.requires_python or install.version_str in spec.requires_python_spec:
                python_exe = install.executable
                python_version = install.version_str
                break
        else:
            raise PythonVersionNotFound(
                f"Could not find a Python install satisfying {spec.requires_python!r}."
            )

        # Make the venv
        if os.path.exists(cache_path):
            raise FileExistsError(
                f"Cache path {cache_path!r} already exists. "
                f"Clear caches to resolve."
            )

        try:
            _laz.subprocess.run(
                [python_exe, "-m", "venv", "--upgrade-deps", cache_path],
                check=True
            )
        except _laz.subprocess.CalledProcessError as e:
            raise VenvBuildError(f"Failed to build venv: {e}")

        match sys.platform:
            case "win32":
                venv_exe = os.path.join(cache_path, "Scripts", "python.exe")
            case _:
                venv_exe = os.path.join(cache_path, "bin", "python")

        if spec.dependencies:
            try:
                _laz.subprocess.run(
                    [
                        venv_exe,
                        "-m",
                        "pip",
                        "install",
                        *spec.dependencies
                    ],
                    check=True,
                )
            except _laz.subprocess.CalledProcessError as e:
                raise VenvBuildError(f"Failed to install dependencies: {e}")

            print("installed")

            freeze = _laz.subprocess.run([venv_exe, "-m", "pip", "freeze"], capture_output=True)

            installed_modules = [item for item in freeze.stdout.decode().split(os.linesep) if item]
        else:
            installed_modules = []

        new_cache = CachedEnv(
            cache_name=new_cachename,
            cache_path=venv_exe,
            raw_specs=[spec.raw_spec],
            python_version=python_version,
            installed_modules=installed_modules,
        )

        self.caches[new_cachename] = new_cache
        self.save_cache()

        return new_cache

    def find_or_create_env(self, spec: EnvironmentSpec) -> CachedEnv:
        env = self.find_env(spec) or self.create_env(spec)

        return env
