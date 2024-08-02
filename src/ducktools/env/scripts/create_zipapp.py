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
This is the script that builds the inner ducktools-env folder
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
from importlib.metadata import requires
from packaging.requirements import Requirement

import ducktools.env
from ducktools.env import platform_paths, MINIMUM_PYTHON_STR, bootstrap_requires
from ducktools.env.scripts import get_pip


def build_env_folder(*, clear_old_builds=True):
    # Use the existing Python to build
    python_path = sys.executable
    # pip is needed to build the zipapp
    paths = platform_paths.default_paths

    latest_pip = get_pip.LATEST_PIP
    pip_path = get_pip.retrieve_pip(latest_pip)

    # Get the full requirements for ducktools-env
    deps = []
    reqs = requires("ducktools.env")
    for req in reqs:
        req = Requirement(req)
        if not (req.marker and not req.marker.evaluate({"python_version": MINIMUM_PYTHON_STR})):
            deps.append(f"{req.name}{req.specifier}")

    build_folder = paths.build_folder()

    if clear_old_builds:
        build_folder_path = Path(build_folder)
        for p in build_folder_path.parent.glob("*"):
            if p != build_folder_path:
                shutil.rmtree(p)

    try:
        print("Downloading application dependencies")
        # Pip install packages into build folder
        pip_command = [
            python_path,
            pip_path,
            "--disable-pip-version-check",
            "install",
            *deps,
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
            print("Copying application into archive")
            ignore_compiled = shutil.ignore_patterns("__pycache__")
            shutil.copytree(
                env_folder,
                os.path.join(build_folder, "ducktools", "env"),
                ignore=ignore_compiled,
            )

            main_app_path = env_folder / "__main__.py"
            print("Copying __main__.py into lib")
            shutil.copy(main_app_path, build_folder)

        print("Creating ducktools-env lib folder")
        shutil.rmtree(paths.env_folder, ignore_errors=True)
        shutil.copytree(
            build_folder,
            paths.env_folder,
        )

        print("Writing env version number")
        with open(paths.env_folder + ".version", 'w') as f:
            f.write(ducktools.env.__version__)

    finally:
        pass  # clean up tempdir


def build_zipapp(*, clear_old_builds=True):
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

    print("Copying pip.pyz and ducktools-env")
    shutil.copytree(paths.manager_folder, build_folder, dirs_exist_ok=True)

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
    build_env_folder()
    build_zipapp()
