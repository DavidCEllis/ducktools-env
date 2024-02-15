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

from ducktools.lazyimporter import (
    LazyImporter,
    FromImport,
    ModuleImport,
    MultiFromImport,
)

from prefab_classes import prefab, attribute
import prefab_classes.funcs as prefab_funcs

from .environment_spec import EnvironmentSpec
from .config import Config
from .exceptions import PythonVersionNotFound, InvalidEnvironmentSpec, VenvBuildError, EnvManError

MINIMUM_PIP = "22.3"  # This version of pip introduced --python

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
        MultiFromImport("packaging.version", ["Version", "InvalidVersion"]),
    ]
)


def _datetime_now_iso() -> str:
    """
    Helper function to allow use of datetime.now with iso formatting
    as a default factory
    """
    return _datetime.now().isoformat()


@prefab(kw_only=True)
class CachedEnv:
    cache_name: str
    cache_path: str
    raw_specs: list[str]
    python_version: str
    installed_modules: list[str]
    parent_python: str
    usage_count: int = 0
    created_on: str = attribute(default_factory=_datetime_now_iso)
    last_used: str = attribute(default_factory=_datetime_now_iso)

    @property
    def python_path(self) -> str:
        if sys.platform == "win32":
            return os.path.join(self.cache_path, "Scripts", "python.exe")
        else:
            return os.path.join(self.cache_path, "bin", "python")

    @property
    def created_date(self) -> _datetime:
        return _datetime.fromisoformat(self.created_on)

    @property
    def last_used_date(self) -> _datetime:
        return _datetime.fromisoformat(self.last_used)

    @property
    def exists(self) -> bool:
        return os.path.exists(self.python_path)

    @property
    def parent_exists(self) -> bool:
        return os.path.exists(self.parent_python)

    @property
    def is_valid(self) -> bool:
        """Check that both the folder exists and the source python exists"""
        return self.exists and self.parent_exists

    def delete(self) -> None:
        """Delete the cache folder"""
        _laz.shutil.rmtree(self.cache_path)


@prefab(kw_only=True)
class Catalogue:
    caches: dict[str, CachedEnv]
    config: Config
    # Not the count of current envs
    # This is the total number of envs that have ever been created
    env_counter: int = 1

    def log(self, message):
        return self.config.log(message)

    def save(self) -> None:
        """Serialize this class into a JSON string and save"""
        # For external users that may not import prefab directly
        data = prefab_funcs.to_json(self, excludes=("config",), indent=2)

        os.makedirs(self.config.cache_folder, exist_ok=True)

        with open(self.config.cache_db_path, "w") as f:
            f.write(data)

    def delete_cache(self, cachename: str) -> None:
        if cache := self.caches.get(cachename):
            cache.delete()
            del self.caches[cachename]
            self.save()
        else:
            raise FileNotFoundError(f"Cache {cachename!r} not found")

    def purge_cache_folder(self):
        """
        Clear the cache folder when things have gone wrong or for a new version.
        """
        # Clear the folder
        try:
            _laz.shutil.rmtree(self.config.cache_folder)
        except FileNotFoundError:
            pass

        # Remove caches that no longer exist
        for cache_name, cache in self.caches.copy().items():
            if not cache.is_valid:
                del self.caches[cache_name]

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

    def expire_caches(self) -> None:
        """Delete caches that have 'expired'"""
        if delta := self.config.cache_expires:
            ctime = _datetime.now()
            # Iterate over a copy as we are modifying the original
            for cachename, cache in self.caches.copy().items():
                if (ctime - cache.created_date) > delta:
                    self.delete_cache(cachename)

        self.save()

    @classmethod
    def from_config(cls, config: Config) -> "Catalogue":
        try:
            with open(config.cache_db_path, "r") as f:
                raw_caches = _laz.json.load(f)
        except FileNotFoundError:
            raw_caches = {}

        caches = {
            name: CachedEnv(**cache_info)
            for name, cache_info in raw_caches.get("caches", {}).items()
        }

        env_counter = raw_caches.get("env_counter", 1)

        # noinspection PyArgumentList
        return cls(caches=caches, env_counter=env_counter, config=config)

    def find_exact_env(self, spec: EnvironmentSpec) -> CachedEnv | None:
        """
        Attempt to find a cached python environment that matches the literal text
        of the specification.

        This means that either the exact text was used to generate the environment
        or that it has previously matched in sufficient mode.

        :param spec: EnvironmentSpec of requirements
        :return: CacheFolder details of python env that satisfies it or None
        """
        for cache in self.caches.values():
            if spec.raw_spec in cache.raw_specs:
                cache.last_used = _datetime_now_iso()
                self.save()
                return cache
        else:
            return None

    def find_sufficient_env(self, spec: EnvironmentSpec) -> CachedEnv | None:
        """
        Check for a cache that matches the minimums of all specified modules

        If found, add the text of the spec to raw_specs for that module and return it.

        :param spec: EnvironmentSpec requirements for a python environment
        :return: CacheFolder python environment details or None
        """
        if self.config.exact_match_only:
            raise EnvManError(
                "Can not use 'sufficient' matching environment "
                "if exact match is required."
            )

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
                self.save()
                return cache

        else:
            return None

    def find_env(self, spec: EnvironmentSpec) -> CachedEnv | None:
        """
        Try to find an existing cached environment that satisfies the spec

        :param spec:
        :return:
        """
        env = self.find_exact_env(spec)

        if not (env or self.config.exact_match_only):
            env = self.find_sufficient_env(spec)

        return env

    def create_env(self, spec: EnvironmentSpec) -> CachedEnv:
        # Check the spec is valid
        if spec_errors := spec.errors():
            raise InvalidEnvironmentSpec("; ".join(spec_errors))

        # Delete the oldest cache if there are too many
        while len(self.caches) > self.config.cache_maxsize:
            del_cache = self.oldest_cache
            self.log(f"Deleting {del_cache}")
            self.delete_cache(del_cache)

        new_cachename = f"env_{self.env_counter}"
        self.env_counter += 1
        cache_path = os.path.join(self.config.cache_folder, new_cachename)

        # Find a valid python executable
        for install in _laz.get_python_installs():
            if pip_ver_str := install.get_pip_version():
                pip_ver = _packaging.Version(pip_ver_str)

                if pip_ver < _packaging.Version(MINIMUM_PIP):
                    self.log(
                        f"Version of Python found at {install.executable} "
                        f"has an outdated version of pip which does not have "
                        f"necessary functionality."
                    )
                elif (
                    not spec.requires_python
                    or install.version_str in spec.requires_python_spec
                ):
                    python_exe = install.executable
                    python_version = install.version_str
                    break
            else:
                self.log(f"Python found at {install.executable} did not have pip installed.")
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
            self.log(f"Creating venv in: {cache_path}")
            _laz.subprocess.run(
                [python_exe, "-m", "venv", "--without-pip", cache_path], check=True
            )
        except _laz.subprocess.CalledProcessError as e:
            raise VenvBuildError(f"Failed to build venv: {e}")

        if spec.dependencies:
            dep_list = ", ".join(spec.dependencies)
            self.log(f"Installing dependencies from PyPI: {dep_list}")
            try:
                _laz.subprocess.run(
                    [
                        python_exe,
                        "-m",
                        "pip",
                        "-q",  # Quiet
                        "--python",
                        cache_path,
                        "install",
                        *spec.dependencies,
                    ],
                    check=True,
                )
            except _laz.subprocess.CalledProcessError as e:
                raise VenvBuildError(f"Failed to install dependencies: {e}")

            freeze = _laz.subprocess.run(
                [
                    python_exe,
                    "-m",
                    "pip",
                    "--python",
                    cache_path,
                    "freeze",
                ],
                capture_output=True,
                text=True,
            )

            installed_modules = [
                item for item in freeze.stdout.split(os.linesep) if item
            ]
        else:
            installed_modules = []

        new_cache = CachedEnv(
            cache_name=new_cachename,
            cache_path=cache_path,
            raw_specs=[spec.raw_spec],
            python_version=python_version,
            installed_modules=installed_modules,
            parent_python=python_exe,
        )

        self.caches[new_cachename] = new_cache
        self.save()

        return new_cache

    def find_or_create_env(self, spec: EnvironmentSpec) -> CachedEnv:
        env = self.find_env(spec)
        if not env:
            self.log("Existing environment not found, creating new environment.")
            env = self.create_env(spec)
        return env
