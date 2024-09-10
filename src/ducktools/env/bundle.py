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

import shutil
import subprocess
import sys
import zipapp

from pathlib import Path

import importlib.resources

from . import DATA_BUNDLE_FOLDER, MINIMUM_PYTHON_STR, bootstrap_requires
from .platform_paths import ManagedPaths
from .exceptions import ScriptNameClash
from .environment_specs import EnvironmentSpec

invalid_script_names = {
    "__main__.py",
    "_bootstrap.py",
    "_platform_paths.py",
    "_check_outdated_python.py",
    "_vendor.py",
}


def create_bundle(
    *,
    script_file: str,
    output_file: str | None = None,
    paths: ManagedPaths,
    installer_command: list[str],
    lockdata: str | None = None,
) -> None:
    """
    Create a zipapp bundle for the inline script

    :param script_file: path to the source script file
    :param paths: ManagedPaths object containing application path info
    :param installer_command: appropriate UV or PIP 'install' command
    :param output_file: output path for the bundle, if not provided the
                        scriptfile path will be used with `.pyz` added as
                        file extension
    :param lockdata: Content of lockfile or None
    :raises ScriptNameClash: error raised if the script name clashes with a 
                             name required for bootstrapping.
    """
    script_path = Path(script_file)

    if script_path.suffix in {".pyz", ".pyzw"}:
        sys.stderr.write(
            "Bundles must be created from .py scripts not .pyz[w] archives\n"
        )

    if script_path.name in invalid_script_names:
        raise ScriptNameClash(
            f"Script {script_file!r} can't be bundled as the name clashes with "
            f"a script or library required for unbundling"
        )

    with paths.build_folder() as build_folder:
        build_path = Path(build_folder)
        print(f"Building bundle in {build_folder!r}")
        print("Copying libraries into build folder")
        # Don't copy UV - it's platform dependent
        uv_base_exe = "uv.exe" if sys.platform == "win32" else "uv"
        uv_pattern = shutil.ignore_patterns(uv_base_exe, f"{uv_base_exe}.version")

        # Copy pip and ducktools zipapps into folder
        shutil.copytree(
            paths.manager_folder,
            build_path,
            ignore=uv_pattern,
            dirs_exist_ok=True,
        )

        resources = importlib.resources.files("ducktools.env")

        with importlib.resources.as_file(resources) as env_folder:
            platform_paths_path = env_folder / "platform_paths.py"
            bootstrap_path = env_folder / "bootstrapping" / "bootstrap.py"
            main_zipapp_path = env_folder / "bootstrapping" / "bundle_main.py"
            check_outdated_path = env_folder / "check_outdated_python.py"

            shutil.copy(platform_paths_path, build_path / "_platform_paths.py")
            shutil.copy(bootstrap_path, build_path / "_bootstrap.py")
            shutil.copy(check_outdated_path, build_path / "_check_outdated_python.py")

            # Write __main__.py with script name included
            with open(build_path / "__main__.py", 'w') as main_file:
                main_file.write(main_zipapp_path.read_text())
                main_file.write(f"\nmain({script_path.name!r})\n")

        print("Installing required unpacking libraries")
        vendor_folder = str(build_path / "_vendor")

        # Unpacking libraries use a ducktools determined minimum python
        # This is for the bootstrapping python and not the python that will
        # run the script.
        pip_command = [
            *installer_command,
            "install",
            "-q",
            *bootstrap_requires,
            "--python-version",
            MINIMUM_PYTHON_STR,
            "--only-binary=:all:",
            "--no-compile",
            "--target",
            vendor_folder
        ]

        subprocess.run(pip_command)

        if lockdata:
            # Copy the lockfile to the lock folder
            lock_path = Path(build_path) / f"{script_path.name}.lock"
            lock_path.write_text(lockdata)

        print("Copying script to build folder and bundling")
        shutil.copy(script_path, build_path)

        spec = EnvironmentSpec.from_script(script_path)
        if sources := spec.details.data_sources:
            print("Bundling additional data")
            data_folder = build_path / DATA_BUNDLE_FOLDER
            data_folder.mkdir()

            for p in sources:
                pth = Path(script_file).parent / p
                if pth.is_file():
                    shutil.copy(pth, data_folder)
                elif pth.is_dir():
                    shutil.copytree(pth, data_folder / pth.name)

        if output_file is None:
            archive_path = Path(script_file).with_suffix(".pyz")
        else:
            archive_path = Path(output_file)

        zipapp.create_archive(
            source=build_folder,
            target=archive_path,
            interpreter="/usr/bin/env python",
        )

    print(f"Bundled {script_file!r} as '{archive_path}'")
