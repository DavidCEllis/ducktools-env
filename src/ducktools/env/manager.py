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
import sys
import os
import os.path

from ducktools.classbuilder.prefab import Prefab, attribute
from ducktools.lazyimporter import LazyImporter, FromImport, MultiFromImport

from . import (
    FOLDER_ENVVAR,
    PROJECT_NAME,
    APP_COMMAND,
    DATA_BUNDLE_ENVVAR,
    DATA_BUNDLE_FOLDER,
    LAUNCH_ENVIRONMENT_ENVVAR,
    LAUNCH_PATH_ENVVAR,
    LAUNCH_TYPE_ENVVAR,
    __version__,
)
from .config import Config
from .platform_paths import ManagedPaths
from .catalogue import TemporaryCatalogue, ApplicationCatalogue
from .environment_specs import EnvironmentSpec
from .exceptions import (
    InvalidEnvironmentSpec,
    PythonVersionNotFound,
    ScriptNotFound,
)
from .register import RegisterManager, RegisteredScript

from ._lazy_imports import laz as _laz
from ._logger import log


_laz_internal = LazyImporter(
    [
        FromImport(".bundle", "create_bundle"),
        FromImport(".scripts.get_pip", "retrieve_pip"),
        MultiFromImport(
            ".scripts.get_uv",
            ["retrieve_uv", "get_available_pythons", "install_uv_python"]
        ),
        MultiFromImport(
            ".scripts.create_zipapp",
            ["build_env_folder", "build_zipapp"]
        ),
    ],
    globs=globals(),
)


class Manager(Prefab):
    project_name: str = PROJECT_NAME
    config: Config = None
    command: str | None = None

    paths: ManagedPaths = attribute(init=False, repr=False)
    _temp_catalogue: TemporaryCatalogue | None = attribute(default=None, private=True)
    _app_catalogue: ApplicationCatalogue | None = attribute(default=None, private=True)
    _script_registry: RegisterManager | None = attribute(default=None, private=True)

    def __prefab_post_init__(self, config, command):
        self.paths = ManagedPaths(self.project_name)
        self.config = Config.load(self.paths.config_path) if config is None else config
        self.command = command if command else APP_COMMAND

    @property
    def temp_catalogue(self) -> TemporaryCatalogue:
        if self._temp_catalogue is None:
            self._temp_catalogue = TemporaryCatalogue(path=self.paths.cache_db)

            # Clear expired caches on load
            self._temp_catalogue.expire_caches(self.config.cache_lifetime_delta)
        return self._temp_catalogue

    @property
    def app_catalogue(self) -> ApplicationCatalogue:
        if self._app_catalogue is None:
            self._app_catalogue = ApplicationCatalogue(path=self.paths.application_db)
        return self._app_catalogue

    @property
    def script_registry(self) -> RegisterManager:
        if self._script_registry is None:
            self._script_registry = RegisterManager(path=self.paths.register_db)
        return self._script_registry

    @property
    def is_installed(self):
        return os.path.exists(self.paths.pip_zipapp) and os.path.exists(self.paths.env_folder)

    @property
    def install_outdated(self):
        """
        Return True if the version running this script is newer than the version
        installed in the cache.
        """
        this_ver = __version__
        installed_ver = self.paths.get_env_version()
        if this_ver == installed_ver:
            return False
        elif _laz.Version(installed_ver).local:
            # Local versions are *always* outdated
            return True
        else:
            return _laz.Version(this_ver) > _laz.Version(installed_ver)

    # Ducktools build commands
    def retrieve_pip(self) -> str:
        return _laz_internal.retrieve_pip(paths=self.paths)

    def retrieve_uv(self, required=False) -> str | None:
        if self.config.use_uv or required:
            uv_path = _laz_internal.retrieve_uv(paths=self.paths)
        else:
            uv_path = None

        if uv_path is None and required:
            raise RuntimeError(
                "UV is required for this process but is unavailable."
            )

        return uv_path

    def _get_python_install(self, spec: EnvironmentSpec):
        install = None

        # Find a valid python executable
        for inst in _laz.list_python_installs():
            if inst.implementation.lower() != "cpython":
                # Ignore all non cpython installs for now
                continue
            if (
                not spec.details.requires_python
                or spec.details.requires_python_spec.contains(inst.version_str)
            ):
                install = inst
                break
        else:
            # If no Python was matched try to install a matching python from UV
            if (uv_path := self.retrieve_uv()) and self.config.uv_install_python:
                uv_pythons = _laz_internal.get_available_pythons(uv_path)
                matched_python = False
                for ver in uv_pythons:
                    if spec.details.requires_python_spec.contains(ver):
                        # Install matching python
                        _laz_internal.install_uv_python(
                            uv_path=uv_path,
                            version_str=ver,
                        )
                        matched_python = ver
                        break
                if matched_python:
                    # Recover the actual install
                    for inst in _laz.get_installed_uv_pythons():
                        if inst.version_str == matched_python:
                            install = inst
                            break

        if install is None:
            raise PythonVersionNotFound(
                f"Could not find a Python install satisfying {spec.details.requires_python!r}."
            )

        return install

    def install_base_command(self, use_uv=True) -> list[str]:
        # Get the installer command for python packages
        # Pip or the faster uv_pip if it is available
        if use_uv and (uv_path := self.retrieve_uv()):
            return [uv_path, "pip"]
        else:
            pip_path = self.retrieve_pip()
            return [sys.executable, pip_path, "--disable-pip-version-check"]

    def build_env_folder(self, clear_old_builds=True) -> None:
        # build_env_folder will use PIP as uv will fail
        # if there is no environment
        # build-env-folder installs into a target directory
        # instead of using a venv
        base_command = [sys.executable, self.retrieve_pip(), "--disable-pip-version-check"]
        _laz_internal.build_env_folder(
            paths=self.paths,
            install_base_command=base_command,
            clear_old_builds=clear_old_builds,
        )

    def build_zipapp(self, clear_old_builds=True) -> None:
        """Build the ducktools.pyz zipapp"""
        base_command = [sys.executable, self.retrieve_pip(), "--disable-pip-version-check"]
        _laz_internal.build_zipapp(
            paths=self.paths,
            install_base_command=base_command,
            clear_old_builds=clear_old_builds,
        )

    # Install and cleanup commands
    def install(self):
        # Install the ducktools package
        self.build_env_folder(clear_old_builds=True)

    def _spec_from_script(
        self,
        *,
        script_path: str,
        lock_path: str | None = None,
        generate_lock: bool = False,
    ) -> EnvironmentSpec:
        """
        Create a 'spec' file from a script path with lockfile arguments

        :param script_path: Path to the original script
        :param lock_path: Path to either existing lockfile or output path for lockfile
        :param generate_lock: Generate a new lockfile
        :return: EnvironmentSpec for the given script with required lock details
        """

        spec = EnvironmentSpec.from_script(script_path)
        if generate_lock:
            spec.generate_lockdata(uv_path=self.retrieve_uv(required=True))
        elif lock_path:
            with open(lock_path, 'r') as f:
                spec.lockdata = f.read()

        return spec

    # Script running and bundling commands
    def get_script_env(self, spec: EnvironmentSpec):
        # A lot of extra logic is in here to avoid doing work early
        # First try to find environments by matching hashes
        env = self.app_catalogue.find_env_hash(spec=spec)

        if env is None:
            env = self.temp_catalogue.find_env_hash(spec=spec)

        if env is None:
            # No hash matches, need to parse the environment
            if spec.details.app:
                if not spec.lockdata:
                    raise InvalidEnvironmentSpec(
                        "Application scripts require a lockfile"
                    )
                # Request an application environment
                env = self.app_catalogue.find_env(spec=spec)

                base_python = self._get_python_install(spec=spec)

                if not env:
                    env = self.app_catalogue.create_env(
                        spec=spec,
                        config=self.config,
                        uv_path=self.retrieve_uv(),
                        installer_command=self.install_base_command(),
                        base_python=base_python
                    )

            else:
                env = self.temp_catalogue.find_env(spec=spec)
                if not env:
                    log("Existing environment not found, creating new environment.")
                    base_python = self._get_python_install(spec=spec)

                    env = self.temp_catalogue.create_env(
                        spec=spec,
                        config=self.config,
                        uv_path=self.retrieve_uv(),
                        installer_command=self.install_base_command(),
                        base_python=base_python,
                    )
        return env

    def _launch_script(
        self,
        *,
        spec: EnvironmentSpec,
        args: list[str],
        env_vars: dict[str, str] | None = None,
    ) -> None:
        """
        Execute the provided spec with the given arguments

        :param spec: Spec generated from script file
        :param args: Arguments to pass to the script
        :param env_vars: Environment variables to set
        """
        env = self.get_script_env(spec)
        env_vars[FOLDER_ENVVAR] = self.paths.project_folder
        env_vars[LAUNCH_ENVIRONMENT_ENVVAR] = env.path
        log(f"Using environment at: {env.path}")

        # Update environment variables for access from subprocess
        os.environ.update(env_vars)
        _laz.subprocess.run([env.python_path, spec.script_path, *args])

    # DO NOT REMOVE #
    def run_bundled_script(
        self,
        *,
        spec: EnvironmentSpec,
        zipapp_path: str,
        args: list[str],
    ):
        """
        OLD BUNDLE SCRIPT - Used directly by bundles made prior to v0.2.1
        This delegates to the new method but is kept for compatibility.
        """
        self.run_bundle(
            script_path=spec.script_path,
            script_args=args,
            lockdata=spec.lockdata,
            zipapp_path=zipapp_path,
        )

    # Higher level commands - take plain inputs
    def run_bundle(
        self,
        *,
        script_path: str,
        script_args: list[str],
        lockdata: str | None,
        zipapp_path: str,
    ):
        """
        Run a script from a path that has been extracted from a bundle

        :param script_path: Path to the .py script extracted from the bundle
        :param script_args: Arguments to pass to the script
        :param lockdata: lockfile data from the bundle if it exists or None
        :param zipapp_path: Path to the original zipapp
        """
        spec = EnvironmentSpec.from_script(
            script_path=script_path,
            lockdata=lockdata,
        )

        env_vars = {
            LAUNCH_TYPE_ENVVAR: "BUNDLE",
            LAUNCH_PATH_ENVVAR: zipapp_path,
        }

        # If the spec indicates there should be data
        # include the bundle data folder in the archive
        if spec.details.data_sources:
            env_vars[DATA_BUNDLE_ENVVAR] = f"{DATA_BUNDLE_FOLDER}/"

        self._launch_script(
            spec=spec,
            args=script_args,
            env_vars=env_vars,
        )

    def run_script(
        self,
        *,
        script_path: str,
        script_args: list[str],
        generate_lock: bool = False,
        lock_path: str | None = None,
    ):
        """
        Run script specs from regular .py files

        :param script_path: Path to the script to execute
        :param script_args: Other arguments to pass to the script
        :param lock_path: Path to either existing lockfile or output path for lockfile
        :param generate_lock: Generate a new lockfile
        """
        spec = self._spec_from_script(
            script_path=script_path,
            lock_path=lock_path,
            generate_lock=generate_lock,
        )

        if generate_lock:
            spec.generate_lockdata(uv_path=self.retrieve_uv(required=True))
            lock_path = lock_path if lock_path else f"{script_path}.lock"
            with open(lock_path, 'w') as f:
                f.write(spec.lockdata)

        env_vars = {
            LAUNCH_TYPE_ENVVAR: "SCRIPT",
            LAUNCH_PATH_ENVVAR: spec.script_path,
        }

        # Add sources to env variable
        if sources := spec.details.data_sources:
            split_char = ";" if sys.platform == "win32" else ":"
            env_vars[DATA_BUNDLE_ENVVAR] = split_char.join(sources)

        self._launch_script(
            spec=spec,
            args=script_args,
            env_vars=env_vars,
        )

    def create_bundle(
        self,
        *,
        script_path: str,
        with_lock: str | None = None,
        generate_lock: bool = False,
        output_file: str | None = None,
        compressed: bool = False,
    ) -> None:
        """
        Create a zipapp bundle for the provided spec

        :param script_path: Script file to bundle
        :param with_lock: Path to lockfile to use in bundle
        :param generate_lock: Generate a lockfile when bundling
        :param output_file: output path to zipapp bundle (script_file.pyz default)
        :param compressed: Compress the resulting zipapp
        """
        if not self.is_installed or self.install_outdated:
            self.install()

        spec = self._spec_from_script(
            script_path=script_path,
            lock_path=with_lock,
            generate_lock=generate_lock,
        )

        _laz_internal.create_bundle(
            spec=spec,
            output_file=output_file,
            paths=self.paths,
            installer_command=self.install_base_command(use_uv=False),
            compressed=compressed,
        )

    def generate_lockfile(
        self,
        script_path: str,
        lockfile_path: str | None = None
    ) -> str:
        """
        Generate lockfile data and write the output to a file
        
        :param script_path: Path to the source script 
        :param lockfile_path: Path to the output lockfile
        :return: Path to the output lockfile
        """""
        spec = EnvironmentSpec.from_script(script_path=script_path)
        spec.generate_lockdata(uv_path=self.retrieve_uv(required=True))

        lockfile_path = lockfile_path if lockfile_path else f"{script_path}.lock"

        with open(lockfile_path, 'w') as f:
            f.write(spec.lockdata)

        return lockfile_path

    def register_script(
        self,
        *,
        script_path: str,
        script_name: str | None = None,
    ) -> None:
        reg = self.script_registry.add_script(script_path, script_name=script_name)
        log(f"Registered '{reg.path}' as '{reg.name}'")

    def remove_registered_script(self, *, script_name: str):
        self.script_registry.remove_script(script_name=script_name)
        log(f"'{script_name}' is no longer registered.")

    def list_registered_scripts(self) -> list[RegisteredScript]:
        return self.script_registry.list_registered_scripts()

    def run_registered_script(
        self,
        *,
        script_name: str,
        script_args: list[str],
        generate_lock: bool = False,
        lock_path: str | None = None,
    ) -> None:
        try:
            row = self.script_registry.retrieve_script(script_name=script_name)
        except ScriptNotFound as e:
            raise RuntimeError(
                "\n".join(e.args),
                f"Use '{self.command} list --scripts' to show registered scripts",
            )
        except FileNotFoundError as e:
            raise RuntimeError(e.args)

        script_path = row.path

        self.run_script(
            script_path=script_path,
            script_args=script_args,
            generate_lock=generate_lock,
            lock_path=lock_path,
        )

    def clear_temporary_cache(self):
        # Clear the temporary environment cache
        log(f"Deleting temporary caches at \"{self.paths.cache_folder}\"")
        self.temp_catalogue.purge_folder()

    def clear_project_folder(self):
        # Clear the entire ducktools folder
        root_path = self.paths.project_folder
        log(f"Deleting full cache at {root_path!r}")
        _laz.shutil.rmtree(root_path, ignore_errors=True)
