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

import os.path
import shutil
import subprocess
import sys
import zipapp

from pathlib import Path

import importlib_resources

from . import MINIMUM_PYTHON_STR, bootstrap_requires
from .platform_paths import ManagedPaths
from .exceptions import ScriptNameClash

invalid_script_names = {
    "__main__.py",
    "_bootstrap.py",
    "_platform_paths.py",
    "_vendor.py",
}


def create_bundle(
    *,
    script_file: str,
    output_file: str | None = None,
    paths: ManagedPaths,
    installer_command: list[str],
) -> None:
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
        print(f"Building bundle in {build_path!r}")
        print("Copying libraries into build folder")
        # Copy pip and ducktools zipapps into folder
        shutil.copytree(paths.manager_folder, build_path, dirs_exist_ok=True)

        resources = importlib_resources.files("ducktools.env")

        with importlib_resources.as_file(resources) as env_folder:
            platform_paths_path = env_folder / "platform_paths.py"
            bootstrap_path = env_folder / "bootstrapping" / "bootstrap.py"
            main_zipapp_path = env_folder / "bootstrapping" / "bundle_main.py"

            shutil.copy(platform_paths_path, build_path / "_platform_paths.py")
            shutil.copy(bootstrap_path, build_path / "_bootstrap.py")

            # Write __main__.py with script name included
            with open(build_path / "__main__.py", 'w') as main_file:
                main_file.write(main_zipapp_path.read_text())
                main_file.write(f"\nmain({script_path.name!r})\n")

        print("Installing required unpacking libraries")
        vendor_folder = str(build_path / "_vendor")

        pip_command = [
            *installer_command,
            "install",
            *bootstrap_requires,
            "--python-version",
            MINIMUM_PYTHON_STR,
            "--only-binary=:all:",
            "--no-compile",
            "--target",
            vendor_folder
        ]

        subprocess.run(pip_command)

        freeze_command = [
            *installer_command,
            "freeze",
            "--path",
            vendor_folder,
        ]

        freeze = subprocess.run(freeze_command, capture_output=True, text=True)
        (Path(vendor_folder) / "requirements.txt").write_text(freeze.stdout)

        print("Copying script to build folder and bundling")
        shutil.copy(script_path, build_path)

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
