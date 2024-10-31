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

from ducktools.classbuilder.prefab import prefab

from ._sqlclasses import SQLAttribute, SQLClass, SQLContext
from .exceptions import InvalidEnvironmentSpec, VenvBuildError, ApplicationError
from .environment_specs import EnvironmentSpec
from .config import Config
from ._logger import log


from ._lazy_imports import laz as _laz


def _datetime_now_iso() -> str:
    """
    Helper function to allow use of datetime.now with iso formatting
    as a default factory
    """
    return _datetime.now().isoformat()


class BaseEnvironment(SQLClass):
    row_id: int = SQLAttribute(default=None, primary_key=True)
    name: str = SQLAttribute(unique=True)
    path: str
    python_version: str
    parent_python: str
    created_on: str = SQLAttribute(default_factory=_datetime_now_iso)
    last_used: str = SQLAttribute(default_factory=_datetime_now_iso, compare=False)
    
    # This field is used to indicate that the venv is usable in case another process
    # Attempts to run a script from the venv before it has finished construction
    # This is False initially and set to True after dependencies are installed
    completed: bool = False  # Actually stored as INT

    spec_hashes: list[str]
    lock_hash: str | None = None
    installed_modules: list[str] = SQLAttribute(default_factory=list)

    @property
    def python_path(self) -> str:
        if sys.platform == "win32":
            if sys.stdout:
                return os.path.join(self.path, "Scripts", "python.exe")
            else:
                return os.path.join(self.path, "Scripts", "pythonw.exe")
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

    @property
    def base_path(self) -> str:
        # Override if there is a parent folder to the environment
        return self.path


class TemporaryEnvironment(BaseEnvironment):
    """
    This is for temporary environments that expire after a certain period
    """
    name: str | None = SQLAttribute(
        default=None,
        computed="'env_' || CAST(row_id AS STRING)",
        unique=True,
    )
    root_path: str

    path: str | None = SQLAttribute(
        default=None,
        unique=True,
        computed=f"root_path || '{os.sep}' || name"
    )


class ApplicationEnvironment(BaseEnvironment):
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

    @property
    def base_path(self) -> str:
        # Apps are in a /env subfolder, this gets the parent app folder
        return os.path.normpath(os.path.join(self.path, os.path.pardir))


@prefab(kw_only=True)
class BaseCatalogue:
    ENV_TYPE = BaseEnvironment
    path: str

    def __init__(self, *, path: str):
        raise RuntimeError("BaseCatalogue should not be initialized")

    def __prefab_post_init__(self):
        # Migration code from JSON catalogue to SQL catalogue
        base_name = os.path.splitext(self.path)[0]
        if os.path.exists(f"{base_name}.json"):
            log("Old JSON environment cache detected, clearing folder.")
            self.purge_folder()

    @property
    def catalogue_folder(self):
        return os.path.dirname(self.path)

    @property
    def connection(self):
        # Create the database if it does not exist
        if not os.path.exists(self.path):
            os.makedirs(os.path.dirname(self.path), exist_ok=True)
            with SQLContext(self.path) as con:
                self.ENV_TYPE.create_table(con)

        return SQLContext(self.path)

    @property
    def environments(self) -> dict[str, ENV_TYPE]:
        with self.connection as con:
            return {
                env.name: env
                for env in self.ENV_TYPE.select_rows(con)
            }

    def env_by_name(self, envname: str) -> ENV_TYPE:
        with self.connection as con:
            return self.ENV_TYPE.select_row(
                con,
                filters={"name": envname}
            )

    def delete_env(self, envname: str) -> None:
        if env := self.env_by_name(envname):
            _laz.shutil.rmtree(env.path)
            with self.connection as con:
                env.delete_row(con)
        else:
            raise FileNotFoundError(f"Cache {envname!r} not found")

    def purge_folder(self):
        """
        Clear the cache folder when things have gone wrong or for a new version.
        """
        # Clear the folder, by its nature this also deletes the database

        try:
            _laz.shutil.rmtree(self.catalogue_folder)
        except FileNotFoundError:  # pragma: no cover
            pass

    def find_env_hash(self, *, spec: EnvironmentSpec) -> ENV_TYPE | None:
        """
        Attempt to find a cached python environment that matches the hash
        of the specification.

        This means that either the exact text was used to generate the environment
        or that it has previously matched in sufficient mode.

        :param spec: EnvironmentSpec of requirements
        :return: CacheFolder details of python env that satisfies it or None
        """
        filters = {
            "spec_hashes": f"%{spec.spec_hash}%"
        }
        with self.connection as con:
            caches = self.ENV_TYPE.select_like(con, filters)

            for cache in caches:
                if not cache.completed:
                    # Ignore venvs that are still being built
                    continue

                if spec.lock_hash and (spec.lock_hash != cache.lock_hash):
                    log(f"Input spec matched {cache.name}, but lockfile did not match.")
                    continue

                log(f"Hash {spec.spec_hash!r} matched environment {cache.name}")

                if not cache.is_valid:
                    log(f"Cache {cache.name!r} does not point to a valid python, removing.")
                    self.delete_env(cache.name)
                    continue

                cache.last_used = _datetime_now_iso()
                cache.update_row(con, ["last_used"])

                return cache
            else:
                return None

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

            if spec.lockdata:
                log("Downloading and installing locked dependencies...")
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
                log(f"Installing dependencies from PyPI: {dep_list}")
                try:
                    if uv_path:
                        dependency_command = [
                            *installer_command,
                            "install",
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

        env.completed = True

        with self.connection as con:
            env.update_row(con, ["installed_modules", "completed"])


@prefab(kw_only=True)
class TemporaryCatalogue(BaseCatalogue):
    """
    Catalogue for temporary environments
    """
    ENV_TYPE = TemporaryEnvironment

    # In theory some of the datetime work could now be done in sqlite
    # But just keep the same logic as for JSON for now

    @property
    def oldest_cache(self) -> str | None:
        """
        :return: name of the oldest cache or None if there are no caches
        """

        old_cache = None
        with self.connection as con:
            caches = self.ENV_TYPE.select_rows(con)

        for cache in caches:
            if old_cache:
                if cache.last_used_date < old_cache.last_used_date:
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
        filters = {"lock_hash": spec.lock_hash}
        with self.connection as con:
            lock_caches = self.ENV_TYPE.select_rows(con, filters)

        for cache in lock_caches:
            if not cache.completed:
                # Ignore environments that are still being built
                continue

            if cache.python_version in spec.details.requires_python_spec:

                if not cache.is_valid:
                    log(f"Cache {cache.name!r} does not point to a valid python, removing.")
                    self.delete_env(cache.name)
                    continue

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
            if not cache.completed:
                # Ignore environments that are still being built
                continue

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

                if spec.spec_hash not in cache.spec_hashes:
                    # If for whatever reason this has been called when hash matches
                    # Don't add the same hash multiple times.
                    cache.spec_hashes.append(spec.spec_hash)

                with self.connection as con:
                    cache.update_row(con, ["last_used", "spec_hashes"])

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
        base_python,
    ) -> ENV_TYPE:
        # Check the spec is valid
        if spec_errors := spec.details.errors():
            raise InvalidEnvironmentSpec("; ".join(spec_errors))

        # Delete the oldest cache if there are too many
        while len(self.environments) >= config.cache_maxcount:
            del_cache = self.oldest_cache
            log(f"Deleting {del_cache}")
            self.delete_env(del_cache)

        with self.connection as con:

            # Construct the Env
            # noinspection PyArgumentList
            new_env = self.ENV_TYPE(
                root_path=self.catalogue_folder,
                python_version=base_python.version_str,
                parent_python=base_python.executable,
                spec_hashes=[spec.spec_hash],
                lock_hash=spec.lock_hash,
            )

            new_env.insert_row(con)

        try:
            self._create_venv(
                spec=spec,
                uv_path=uv_path,
                installer_command=installer_command,
                env=new_env,
            )
        except Exception:
            with self.connection as con:
                new_env.delete_row(con)
            raise

        return new_env


@prefab(kw_only=True)
class ApplicationCatalogue(BaseCatalogue):
    ENV_TYPE = ApplicationEnvironment

    def find_env_hash(self, *, spec: EnvironmentSpec) -> ENV_TYPE | None:
        env: ApplicationEnvironment | None = super().find_env_hash(spec=spec)

        if env:
            # Need to check the lockfile hasn't changed if a match is found
            # The version should be the same if the hash matched
            # as the version is included in the hash
            if spec.lock_hash != env.lock_hash:
                if env.version_spec.is_prerelease:
                    log(
                        "Lockfile or Python version does not match, but version is prerelease.\n"
                        "Clearing outdated environment."
                    )
                    self.delete_env(env.name)
                    env = None
                else:
                    raise ApplicationError(
                        "Application version is the same as the environment "
                        "but the lockfile or Python version does not match."
                    )

        return env

    def find_env(self, spec: EnvironmentSpec) -> ENV_TYPE | None:
        details = spec.details

        env = None

        if cache := self.environments.get(details.app.appkey):
            if not cache.completed:
                # Perhaps it should check the age of the env to decide if it should wait
                # and see if the env has been created?
                raise RuntimeError(
                    f"Environment \"{cache.name}\" has not been completed. "
                    "Either it is currently being built by another process "
                    "or the build has failed and the environment needs to be deleted."
                )

            # Logic is a bit long here because if the versions match we want to
            # avoid generating the packaging.version. Otherwise we would check
            # for the outdated version first.
            if not cache.is_valid:
                log(f"Cache {cache.name!r} does not point to a valid python, removing.")
                self.delete_env(cache.name)

            elif (
                spec.lock_hash == cache.lock_hash
                and spec.details.requires_python_spec.contains(cache.python_version)
            ):
                if details.app.version == cache.version:
                    cache.last_used = _datetime_now_iso()
                    cache.spec_hashes.append(spec.spec_hash)
                    env = cache

                    with self.connection as con:
                        cache.update_row(
                            con,
                            ["last_used", "spec_hashes"]
                        )
                elif details.app.version_spec >= cache.version_spec:
                    # Allow for the version spec to be equal
                    cache.last_used = _datetime_now_iso()
                    cache.version = details.app.version
                    # Update hashed specs for cache
                    if details.app.version_spec == cache.version_spec:
                        cache.spec_hashes.append(spec.spec_hash)
                    else:
                        cache.spec_hashes = [spec.spec_hash]

                    with self.connection as con:
                        cache.update_row(
                            con,
                            ["last_used", "spec_hashes", "version"]
                        )
                    env = cache
                else:
                    raise ApplicationError(
                        f"Attempted to launch older version of application "
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
                            "Lockfile or Python version does not match, but version is prerelease.\n"
                            "Clearing outdated environment."
                        )
                        self.delete_env(cache.name)
                    else:
                        raise ApplicationError(
                            "Application version is the same as the environment "
                            "but the lockfile or Python version does not match."
                        )
                elif details.app.version_spec > cache.version_spec:
                    log("Updating application environment")
                    self.delete_env(cache.name)
                else:
                    raise ApplicationError(
                        f"Attempted to launch older version of application "
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
        base_python,
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

        # noinspection PyArgumentList
        new_env = self.ENV_TYPE(
            name=details.app.appkey,
            path=env_path,
            python_version=base_python.version_str,
            parent_python=base_python.executable,
            spec_hashes=[spec.spec_hash],
            lock_hash=spec.lock_hash,
            owner=details.app.owner,
            appname=details.app.appname,
            version=details.app.version,
        )

        with self.connection as con:
            new_env.insert_row(con)

        try:
            self._create_venv(
                spec=spec,
                uv_path=uv_path,
                installer_command=installer_command,
                env=new_env,
            )
        except Exception:
            with self.connection as con:
                new_env.delete_row(con)
            raise

        return new_env
