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

from ducktools.classbuilder.prefab import Prefab, prefab, attribute, as_dict, get_attributes

from .exceptions import PythonVersionNotFound, InvalidEnvironmentSpec, VenvBuildError, ApplicationError
from .environment_specs import EnvironmentSpec
from .config import Config, log


from ._lazy_imports import laz as _laz


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

    spec_hashes: list[str]
    lock_hash: str | None = None
    installed_modules: list[str] = attribute(default_factory=list)

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
    def last_used_simple(self) -> str:
        """last used date without the sub-second part"""
        return self.last_used_date.strftime("%Y-%m-%d %H:%M:%S")

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


class ApplicationEnv(BaseEnv, kw_only=True):
    """
    Environment for permanent applications that do not get outdated
    """
    owner: str
    appname: str
    version: str

    @property
    def version_spec(self):
        return _laz.Version(self.version)

    def is_outdated(self, spec_version: str):
        # If strings are equal, skip packaging overhead
        if self.version == spec_version:
            return False
        else:
            return _laz.Version(spec_version) > self.version_spec


@prefab(kw_only=True)
class BaseCatalogue:
    ENV_TYPE = BaseEnv

    path: str
    environments: dict[str, ENV_TYPE] = attribute(default_factory=dict)

    @property
    def catalogue_folder(self):
        return os.path.dirname(self.path)

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

    def delete_env(self, envname: str) -> None:
        if env := self.environments.get(envname):
            env.delete()
            del self.environments[envname]
            self.save()
        else:
            raise FileNotFoundError(f"Cache {envname!r} not found")

    def purge_folder(self):
        """
        Clear the cache folder when things have gone wrong or for a new version.
        """
        # This does not save as the act of deleting the catalogue folder 
        # will delete the file. It should not automatically be recreated.

        # Clear the folder
        try:
            _laz.shutil.rmtree(self.catalogue_folder)
        except FileNotFoundError:  # pragma: no cover
            pass

        # Clear environment list
        self.environments = {}

    def find_env_hash(self, *, spec: EnvironmentSpec) -> ENV_TYPE | None:
        """
        Attempt to find a cached python environment that matches the hash
        of the specification.

        This means that either the exact text was used to generate the environment
        or that it has previously matched in sufficient mode.

        :param spec: EnvironmentSpec of requirements
        :return: CacheFolder details of python env that satisfies it or None
        """
        for cache in self.environments.values():
            if spec.spec_hash in cache.spec_hashes:
                if spec.lock_hash and (spec.lock_hash != cache.lock_hash):
                    log(f"Input spec matched {cache.name}, but lockfile did not match.")
                    continue

                log(f"Hash {spec.spec_hash!r} matched environment {cache.name}")

                if not cache.is_valid:
                    log(f"Cache {cache.name!r} does not point to a valid python, removing.")
                    self.delete_env(cache.name)
                    continue

                cache.last_used = _datetime_now_iso()
                self.save()
                return cache
        else:
            return None

    @staticmethod
    def _get_python_install(spec: EnvironmentSpec):
        # Find a valid python executable
        for install in _laz.list_python_installs():
            if install.implementation.lower() != "cpython":
                # Ignore all non cpython installs for now
                continue
            if (
                not spec.details.requires_python
                or spec.details.requires_python_spec.contains(install.version_str, prereleases=True)
            ):
                break
        else:
            raise PythonVersionNotFound(
                f"Could not find a Python install satisfying {spec.details.requires_python!r}."
            )

        return install

    def _create_venv(
        self,
        *,
        spec: EnvironmentSpec,
        uv_path: str | None,
        installer_command: list[str],
        env: ENV_TYPE,
    ):
        if os.path.exists(env.path):
            raise FileExistsError(
                f"Install path {env.path!r} already exists. "
                f"Uninstall application to resolve."
            )

        python_exe = env.parent_python

        # Build the venv folder
        try:
            log(f"Creating venv in: {env.path}")
            if uv_path:
                _laz.subprocess.run(
                    [uv_path, "venv", "-q", "--python", python_exe, env.path], check=True
                )
            else:
                _laz.subprocess.run(
                    [python_exe, "-m", "venv", "--without-pip", env.path], check=True
                )
        except _laz.subprocess.CalledProcessError as e:
            # Try to delete the folder if it exists
            _laz.shutil.rmtree(env.path, ignore_errors=True)
            raise VenvBuildError(f"Failed to build venv: {e}")

        if deps := spec.details.dependencies:
            dep_list = ", ".join(deps)
            log(f"Installing dependencies from PyPI: {dep_list}")

            if spec.lockdata:
                log("Using lockfile")
                # Need a temporary file to use as the lockfile
                with _laz.tempfile.TemporaryDirectory() as tempfld:
                    requirements_path = os.path.join(tempfld, "requirements.txt")
                    with open(requirements_path, 'w') as f:
                        f.write(spec.lockdata)
                    try:
                        if uv_path:
                            dependency_command = [
                                *installer_command,
                                "install",
                                "-q",  # Quiet
                                "--python",
                                env.python_path,
                                "-r",
                                requirements_path,
                            ]
                        else:
                            dependency_command = [
                                *installer_command,
                                "--python",
                                env.python_path,
                                "install",
                                "-q",  # Quiet
                                "-r",
                                requirements_path,
                            ]
                        _laz.subprocess.run(
                            dependency_command,
                            check=True,
                        )
                    except _laz.subprocess.CalledProcessError as e:
                        # Try to delete the folder if it exists
                        _laz.shutil.rmtree(env.path, ignore_errors=True)
                        raise VenvBuildError(f"Failed to install dependencies: {e}")
            else:
                try:
                    if uv_path:
                        dependency_command = [
                            *installer_command,
                            "install",
                            "-q",  # Quiet
                            "--python",
                            env.python_path,
                            *deps,
                        ]
                    else:
                        dependency_command = [
                            *installer_command,
                            "--python",
                            env.python_path,
                            "install",
                            "-q",  # Quiet
                            *deps,
                        ]
                    _laz.subprocess.run(
                        dependency_command,
                        check=True,
                    )
                except _laz.subprocess.CalledProcessError as e:
                    # Try to delete the folder if it exists
                    _laz.shutil.rmtree(env.path, ignore_errors=True)
                    raise VenvBuildError(f"Failed to install dependencies: {e}")

            # Get pip-freeze list to use for installed modules
            if uv_path:
                freeze_command = [
                    *installer_command,
                    "freeze",
                    "--python",
                    env.python_path,
                ]
            else:
                freeze_command = [
                    *installer_command,
                    "--python",
                    env.python_path,
                    "freeze",
                ]
            freeze = _laz.subprocess.run(
                freeze_command,
                capture_output=True,
                text=True,
            )

            installed_modules = [
                item.strip()
                for item in freeze.stdout.splitlines()
                if item
            ]

            env.installed_modules.extend(installed_modules)

        self.environments[env.name] = env
        self.save()


@prefab(kw_only=True)
class TempCatalogue(BaseCatalogue):
    """
    Catalogue for temporary environments
    """
    ENV_TYPE = TemporaryEnv

    environments: dict[str, ENV_TYPE] = attribute(default_factory=dict)
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

    def find_locked_env(
        self,
        *,
        spec: EnvironmentSpec,
    ) -> ENV_TYPE | None:
        """
        Find a cached TemporaryEnv that matches the hash of the lockfile

        :param spec: Environment specification (needed for lock)
        :return: TemporaryEnv environment or None
        """
        # Get lock data hash
        for cache in self.environments.values():
            if (
                cache.lock_hash == spec.lock_hash
                and cache.python_version in spec.details.requires_python_spec
            ):
                log(f"Lockfile hash {spec.lock_hash!r} matched environment {cache.name}")
                cache.last_used = _datetime_now_iso()
                return cache
        else:
            return None

    def find_sufficient_env(self, *, spec: EnvironmentSpec) -> ENV_TYPE | None:
        """
        Check for a cache that matches the minimums of all specified modules

        If found, add the text of the spec to raw_specs for that module and return it.

        :param spec: EnvironmentSpec requirements for a python environment
        :return: TemporaryEnv environment or None
        """

        for cache in self.environments.values():
            # If no python version listed ignore it
            # If python version is listed, make sure it matches
            if spec.details.requires_python:
                cache_pyver = _laz.Version(cache.python_version)
                if not spec.details.requires_python_spec.contains(cache_pyver, prereleases=True):
                    continue

            # Check dependencies
            cache_spec = {}

            for mod in cache.installed_modules:
                name, version = mod.split("==")
                # There should only be one specifier, specifying one version
                module_ver = _laz.Version(version)
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

                if not cache.is_valid:
                    log(f"Cache {cache.name!r} does not point to a valid python, removing.")
                    self.delete_env(cache.name)
                    continue

                log(f"Adding {spec.spec_hash!r} to {cache.name!r} hash list")

                cache.last_used = _datetime_now_iso()
                cache.spec_hashes.append(spec.spec_hash)

                self.save()
                return cache

        else:
            return None

    def find_env(self, *, spec: EnvironmentSpec) -> ENV_TYPE | None:
        """
        Try to find an existing cached environment that satisfies the spec

        :param spec: Environment specification
        :return: TemporaryEnv environment or None
        """
        if spec.lock_hash:
            env = self.find_locked_env(spec=spec)
        else:
            env = self.find_sufficient_env(spec=spec)

        return env

    def create_env(
        self,
        *,
        spec: EnvironmentSpec,
        config: Config,
        uv_path: str | None,
        installer_command: list[str],
    ) -> ENV_TYPE:
        # Check the spec is valid
        if spec_errors := spec.details.errors():
            raise InvalidEnvironmentSpec("; ".join(spec_errors))

        # Delete the oldest cache if there are too many
        while len(self.environments) >= config.cache_maxcount:
            del_cache = self.oldest_cache
            log(f"Deleting {del_cache}")
            self.delete_env(del_cache)

        new_cachename = f"env_{self.env_counter}"
        self.env_counter += 1

        cache_path = os.path.join(self.catalogue_folder, new_cachename)

        install = self._get_python_install(spec)

        # Construct the Env
        # noinspection PyArgumentList
        new_env = self.ENV_TYPE(
            name=new_cachename,
            path=cache_path,
            python_version=install.version_str,
            parent_python=install.executable,
            spec_hashes=[spec.spec_hash],
            lock_hash=spec.lock_hash,
        )

        self._create_venv(
            spec=spec,
            uv_path=uv_path,
            installer_command=installer_command,
            env=new_env,
        )

        return new_env


@prefab(kw_only=True)
class ApplicationCatalogue(BaseCatalogue):
    ENV_TYPE = ApplicationEnv

    environments: dict[str, ENV_TYPE] = attribute(default_factory=dict)

    def find_env_hash(self, *, spec: EnvironmentSpec) -> ENV_TYPE | None:
        env: ApplicationEnv | None = super().find_env_hash(spec=spec)

        if env:
            # Need to check the lockfile hasn't changed if a match is found
            # The version should be the same if the hash matched
            # as the version is included in the hash
            if spec.lock_hash != env.lock_hash:
                log("Spec matching but lockfile outdated, purging old environment")
                self.delete_env(env.name)
                env = None

        return env

    def find_env(self, spec: EnvironmentSpec) -> ENV_TYPE | None:
        details = spec.details

        env = None

        if cache := self.environments.get(details.app.appkey):
            # Logic is a bit long here because if the versions match we want to
            # avoid generating the packaging.version. Otherwise we would check
            # for the outdated version first.

            if spec.lock_hash == cache.lock_hash:
                if details.app.version == cache.version:
                    cache.last_used = _datetime_now_iso()
                    env = cache
                elif details.app.version_spec >= cache.version_spec:
                    # Allow for the version spec to be equal
                    cache.last_used = _datetime_now_iso()
                    env = cache
                    env.version = details.app.version
                else:
                    raise ApplicationError(
                        f"Attempted to launch older version of application"
                        f"when newer version has been installed. \n"
                        f"app version: {details.app.version} \n"
                        f"installed version: {cache.version}"
                    )
            else:
                # Lock file does not match
                if (
                    details.app.version == cache.version
                    or details.app.version_spec == cache.version_spec
                ):
                    # Equal spec is also a failure if lockfile does not match
                    if cache.version_spec.is_prerelease:
                        log(
                            "Lockfile does not match, but version is prerelease.\n"
                            "Clearing outdated environment."
                        )
                        self.delete_env(cache.name)
                    else:
                        raise ApplicationError(
                            "Application version is the same as the environment "
                            "but the lockfile does not match."
                        )
                elif details.app.version_spec > cache.version_spec:
                    log("Updating application environment")
                    self.delete_env(cache.name)
                else:
                    raise ApplicationError(
                        f"Attempted to launch older version of application"
                        f"when newer version has been installed. \n"
                        f"app version: {details.app.version} \n"
                        f"installed version: {cache.version}"
                    )

        return env

    def create_env(
        self,
        *,
        spec: EnvironmentSpec,
        config: Config,
        uv_path: str,
        installer_command: list[str],
    ):
        if not spec.lockdata:
            raise ApplicationError("Application environments require a lockfile.")

        # Check the spec is valid
        if spec_errors := spec.details.errors():
            raise InvalidEnvironmentSpec("; ".join(spec_errors))

        details = spec.details

        try:
            _ = details.app.version_spec
        except _laz.InvalidVersion:
            raise ApplicationError(
                f"Application version: {details.app.version!r} "
                f"is not a valid version specifier."
            )

        env_path = os.path.join(
            self.catalogue_folder,
            details.app.owner,
            details.app.appname,
            "env",
        )

        install = self._get_python_install(spec)

        # noinspection PyArgumentList
        new_env = self.ENV_TYPE(
            name=details.app.appkey,
            path=env_path,
            python_version=install.version,
            parent_python=install.executable,
            spec_hashes=[spec.spec_hash],
            lock_hash=spec.lock_hash,
            owner=details.app.owner,
            appname=details.app.appname,
            version=details.app.version,
        )

        self._create_venv(
            spec=spec,
            uv_path=uv_path,
            installer_command=installer_command,
            env=new_env,
        )

        return new_env
