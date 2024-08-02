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

"""
This is the script that builds the inner ducktools-env.pyz zipapp
and bundles ducktools-env into ducktools.pyz
"""
import os
import os.path
import shutil
import subprocess
import sys
import zipapp

from pathlib import Path

import importlib_resources

import ducktools.env
from ducktools.env import platform_paths, MINIMUM_PYTHON_STR, bootstrap_requires
from ducktools.env.scripts import get_pip


def build_env_zipapp(wheel_path, *, clear_old_builds=True):
    # Just use the existing Python to build
    python_path = sys.executable
    # pip is needed to build the zipapp
    paths = platform_paths.default_paths

    latest_pip = get_pip.LATEST_PIP
    pip_path = get_pip.retrieve_pip(latest_pip)

    build_folder = paths.build_folder()

    if clear_old_builds:
        build_folder_path = Path(build_folder)
        for p in build_folder_path.parent.glob("*"):
            if p != build_folder_path:
                shutil.rmtree(p)

    try:
        print("Downloading application modules")
        print(pip_path)
        # Pip install packages into build folder
        pip_command = [
            python_path,
            pip_path,
            "--disable-pip-version-check",
            "install",
            wheel_path,
            "--python-version",
            MINIMUM_PYTHON_STR,
            "--only-binary=:all:",
            "--no-compile",
            "--target",
            build_folder,
        ]
        subprocess.run(pip_command)

        freeze_command = [
            python_path,
            pip_path,
            "freeze",
            "--path",
            build_folder,
        ]

        freeze = subprocess.run(freeze_command, capture_output=True, text=True)

        (Path(build_folder) / "requirements.txt").write_text(freeze.stdout)

        # Get the paths for modules that need to be copied
        resources = importlib_resources.files("ducktools.env")

        with importlib_resources.as_file(resources) as env_folder:
            main_app_path = env_folder / "__main__.py"

            print("Copying __main__.py into lib")
            shutil.copy(main_app_path, build_folder)

        print("Creating ducktools-env.pyz")
        zipapp.create_archive(
            source=build_folder,
            target=paths.env_zipapp,
            interpreter="/usr/bin/env python"
        )

        print("Writing env version number")
        with open(paths.env_zipapp + ".version", 'w') as f:
            f.write(ducktools.env.__version__)

    finally:
        pass  # clean up tempdir


def build_zipapp(wheel_path, *, clear_old_builds=True):
    # Just use the existing Python to build
    python_path = sys.executable
    # pip is needed to build the zipapp
    paths = platform_paths.default_paths

    latest_pip = get_pip.LATEST_PIP
    pip_path = get_pip.retrieve_pip(latest_pip)

    build_folder = paths.build_folder()

    if clear_old_builds:
        build_folder_path = Path(build_folder)
        for p in build_folder_path.parent.glob("*"):
            if p != build_folder_path:
                shutil.rmtree(p)

    try:
        # Get the paths for modules that need to be copied
        resources = importlib_resources.files("ducktools.env")

        with importlib_resources.as_file(resources) as env_folder:
            platform_paths_path = env_folder / "platform_paths.py"
            bootstrap_path = env_folder / "scripts" / "bootstrap.py"
            main_zipapp_path = env_folder / "scripts" / "zipapp_main.py"

            print("Copying platform paths")
            shutil.copy(platform_paths_path, os.path.join(build_folder, "_platform_paths.py"))

            print("Copying bootstrap script")
            shutil.copy(bootstrap_path, os.path.join(build_folder, "_bootstrap.py"))

            print("Copying __main__ script")
            shutil.copy(main_zipapp_path, os.path.join(build_folder, "__main__.py"))

        print("Copying pip.pyz and ducktools-env.pyz")
        shutil.copytree(paths.manager_folder, build_folder, dirs_exist_ok=True)

        print("Installing bootstrap requirements")
        vendor_folder = os.path.join(build_folder, "_vendor")

        pip_command = [
            python_path,
            pip_path,
            "--disable-pip-version-check",
            "install",
            *bootstrap_requires,
            "--python-version",
            MINIMUM_PYTHON_STR,
            "--only-binary=:all:",
            "--no-compile",
            "--target",
            vendor_folder,
        ]
        subprocess.run(pip_command)

        freeze_command = [
            python_path,
            pip_path,
            "freeze",
            "--path",
            vendor_folder,
        ]

        freeze = subprocess.run(freeze_command, capture_output=True, text=True)

        (Path(vendor_folder) / "requirements.txt").write_text(freeze.stdout)

        dist_folder = Path(__file__).parents[1] / "dist"
        dist_folder.mkdir(exist_ok=True)

        print("Creating ducktools.pyz")
        zipapp.create_archive(
            source=build_folder,
            target=dist_folder / "ducktools.pyz",
            interpreter="/usr/bin/env python"
        )

    finally:
        pass  # clean up tempdir


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(
        description="Create Ducktools Zipapp"
    )

    parser.add_argument(
        "wheel_path",
        help="Path to ducktools.env wheel file or source directory."
    )

    args = parser.parse_args()

    path_base = args.wheel_path

    build_env_zipapp(path_base)
    build_zipapp(path_base)
