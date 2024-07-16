# ducktools.env
# MIT License
#
# Copyright (c) 2024 David C Ellis
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.
from __future__ import annotations

import sys
import os.path
from datetime import datetime as _datetime, timedelta as _timedelta

from ducktools.lazyimporter import (
    LazyImporter,
    FromImport,
    ModuleImport,
    MultiFromImport,
)

from ducktools.classbuilder.prefab import Prefab, prefab, attribute, as_dict, get_attributes

from .exceptions import PythonVersionNotFound, InvalidEnvironmentSpec, VenvBuildError
from .environment_specs import EnvironmentSpec
from .config import Config, log

MINIMUM_PIP = "22.3"  # This version of pip introduced --python

_laz = LazyImporter(
    [
        ModuleImport("shutil"),
        ModuleImport("json"),
        ModuleImport("subprocess"),
        ModuleImport("hashlib"),
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


class BaseEnv(Prefab, kw_only=True):
    name: str
    path: str
    python_version: str
    parent_python: str
    created_on: str = attribute(default_factory=_datetime_now_iso)
    last_used: str = attribute(default_factory=_datetime_now_iso)

    @property
    def python_path(self) -> str:
        if sys.platform == "win32":
            return os.path.join(self.path, "Scripts", "python.exe")
        else:
            return os.path.join(self.path, "bin", "python")

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
        _laz.shutil.rmtree(self.path)


class TemporaryEnv(BaseEnv, kw_only=True):
    """
    This is for temporary environments that expire after a certain period
    """
    spec_hashes: list[str]
    installed_modules: list[str]


class ApplicationEnv(BaseEnv, kw_only=True):
    ...


@prefab(kw_only=True)
class BaseCatalogue:
    ENV_TYPE = BaseEnv

    path: str
    environments: dict[str, BaseEnv] = attribute(default_factory=dict)

    @property
    def catalogue_folder(self):
        return os.path.split(self.path)[0]

    def save(self) -> None:
        """Serialize this class into a JSON string and save"""
        # For external users that may not import prefab directly
        os.makedirs(self.catalogue_folder, exist_ok=True)

        with open(self.path, "w") as f:
            _laz.json.dump(self, f, default=as_dict, indent=2)

    @classmethod
    def load(cls, path):
        try:
            with open(path, 'r') as f:
                json_data = _laz.json.load(f)
        except (FileNotFoundError, _laz.json.JSONDecodeError):
            # noinspection PyArgumentList
            return cls(path=path)
        else:
            cls_keys = {k for k, v in get_attributes(cls).items() if v.init}

            filtered_data = {
                k: v for k, v in json_data.items() if k in cls_keys
            }

            environments = {}
            for k, v in filtered_data.get("environments", {}).items():
                environments[k] = cls.ENV_TYPE(**v)

            filtered_data["environments"] = environments

            # noinspection PyArgumentList
            return cls(**filtered_data)

    def delete_env(self, envpath: str) -> None:
        if env := self.environments.get(envpath):
            env.delete()
            del self.environments[envpath]
            self.save()
        else:
            raise FileNotFoundError(f"Cache {envpath!r} not found")

    def purge_folder(self):
        """
        Clear the cache folder when things have gone wrong or for a new version.
        """
        # Clear the folder
        try:
            _laz.shutil.rmtree(self.catalogue_folder)
        except FileNotFoundError:
            pass

        # Remove caches that no longer exist
        for cache_name, cache in self.environments.copy().items():
            if not cache.is_valid:
                del self.environments[cache_name]


@prefab(kw_only=True)
class TempCatalogue(BaseCatalogue):
    """
    Catalogue for temporary environments
    """
    ENV_TYPE = TemporaryEnv

    environments: dict[str, TemporaryEnv] = attribute(default_factory=dict)
    env_counter: int = 0

    @property
    def oldest_cache(self) -> str | None:
        """
        :return: name of the oldest cache or None if there are no caches
        """
        old_cache = None
        for cache in self.environments.values():
            if old_cache:
                if cache.last_used < old_cache.last_used:
                    old_cache = cache
            else:
                old_cache = cache

        if old_cache:
            return old_cache.name
        else:
            return None

    def expire_caches(self, lifetime: _timedelta) -> None:
        """
        Delete caches that are older than `lifetime`

        :param lifetime: timedelta age after which caches should be deleted
        :type lifetime: _timedelta
        """
        if lifetime:
            ctime = _datetime.now()
            # Iterate over a copy as we are modifying the original
            for cachename, cache in self.environments.copy().items():
                if (ctime - cache.created_date) > lifetime:
                    self.delete_env(cachename)

        self.save()

    def find_env_hash(self, spec: EnvironmentSpec) -> TemporaryEnv | None:
        """
        Attempt to find a cached python environment that matches the hash
        of the specification.

        This means that either the exact text was used to generate the environment
        or that it has previously matched in sufficient mode.

        :param spec: InlineSpec of requirements
        :return: CacheFolder details of python env that satisfies it or None
        """
        for cache in self.environments.values():
            if spec.spec_hash in cache.spec_hashes:
                log(f"Hash {spec.spec_hash} matched environment {cache.name}")
                cache.last_used = _datetime_now_iso()
                self.save()
                return cache
        else:
            return None

    def find_sufficient_env(self, spec: EnvironmentSpec) -> TemporaryEnv | None:
        """
        Check for a cache that matches the minimums of all specified modules

        If found, add the text of the spec to raw_specs for that module and return it.

        :param spec: InlineSpec requirements for a python environment
        :return: CacheFolder python environment details or None
        """

        for cache in self.environments.values():
            # If no python version listed ignore it
            # If python version is listed, make sure it matches
            if spec.details.requires_python:
                cache_pyver = _packaging.Version(cache.python_version)
                if cache_pyver not in spec.details.requires_python_spec:
                    continue

            # Check dependencies
            cache_spec = {}

            for mod in cache.installed_modules:
                name, version = mod.split("==")
                # There should only be one specifier, specifying one version
                module_ver = _packaging.Version(version)
                cache_spec[name] = module_ver

            for req in spec.details.dependencies_spec:
                # If a dependency is not satisfied , break out of this loop
                if ver := cache_spec.get(req.name):
                    if ver not in req.specifier:
                        break
                else:
                    break
            else:
                # If all dependencies were satisfied, the loop completed
                # Update last_used and append the hash of the spec to the spec hashes
                log(f"Spec satisfied by {cache.name!r}")
                log(f"Adding {spec.spec_hash!r} to {cache.name!r} hash list")

                cache.last_used = _datetime_now_iso()
                cache.spec_hashes.append(spec.spec_hash)

                self.save()
                return cache

        else:
            return None

    def find_env(self, spec: EnvironmentSpec) -> TemporaryEnv | None:
        """
        Try to find an existing cached environment that satisfies the spec

        :param spec:
        :return:
        """
        env = self.find_env_hash(spec)

        if not env:
            env = self.find_sufficient_env(spec)

        return env

    def create_env(self, *, spec: EnvironmentSpec, config: Config) -> TemporaryEnv:
        # Check the spec is valid
        if spec_errors := spec.details.errors():
            raise InvalidEnvironmentSpec("; ".join(spec_errors))

        # Delete the oldest cache if there are too many
        while len(self.environments) > config.cache_maxcount:
            del_cache = self.oldest_cache
            log(f"Deleting {del_cache}")
            self.delete_env(del_cache)

        new_cachename = f"env_{self.env_counter}"
        self.env_counter += 1
        cache_path = os.path.join(self.catalogue_folder, new_cachename)

        # Find a valid python executable
        for install in _laz.get_python_installs():
            if pip_ver_str := install.get_pip_version():
                pip_ver = _packaging.Version(pip_ver_str)

                if pip_ver < _packaging.Version(MINIMUM_PIP):
                    log(
                        f"Version of Python found at {install.executable} "
                        f"has an outdated version of pip which does not have "
                        f"necessary functionality."
                    )
                elif (
                    not spec.details.requires_python
                    or install.version_str in spec.details.requires_python_spec
                ):
                    python_exe = install.executable
                    python_version = install.version_str
                    break
            else:
                log(f"Python found at {install.executable} did not have pip installed.")
        else:
            raise PythonVersionNotFound(
                f"Could not find a Python install satisfying {spec.details.requires_python!r}."
            )

        # Make the venv
        if os.path.exists(cache_path):
            raise FileExistsError(
                f"Cache path {cache_path!r} already exists. "
                f"Clear caches to resolve."
            )

        try:
            log(f"Creating venv in: {cache_path}")
            _laz.subprocess.run(
                [python_exe, "-m", "venv", "--without-pip", cache_path], check=True
            )
        except _laz.subprocess.CalledProcessError as e:
            raise VenvBuildError(f"Failed to build venv: {e}")

        if spec.details.dependencies:
            dep_list = ", ".join(spec.details.dependencies)
            log(f"Installing dependencies from PyPI: {dep_list}")
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
                        *spec.details.dependencies,
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

        new_cache = TemporaryEnv(
            name=new_cachename,
            path=cache_path,
            python_version=python_version,
            parent_python=python_exe,
            spec_hashes=[spec.spec_hash],
            installed_modules=installed_modules,
        )

        self.environments[new_cachename] = new_cache
        self.save()

        return new_cache

    def find_or_create_env(self, spec: EnvironmentSpec, config: Config) -> TemporaryEnv:
        env = self.find_env(spec)
        if not env:
            log("Existing environment not found, creating new environment.")
            env = self.create_env(spec=spec, config=config)
        return env
