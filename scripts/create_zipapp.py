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
import importlib_resources
import os
import os.path
import shutil
import subprocess
import sys
import zipapp

from pathlib import Path

import ducktools.env
from ducktools.env import platform_paths, MINIMUM_PYTHON_STR
from ducktools.env.scripts import get_pip


bootstrap_requires = [
    "ducktools-lazyimporter>=0.5.1",
    "packaging>=23.2",
    # "importlib-resources>=6.0",
]


def build_zipapp(wheel_path, *, clear_old_builds=True):
    # Just use the existing Python to build
    python_path = sys.executable
    # pip is needed to build the zipapp
    paths = platform_paths.default_paths

    latest_pip = get_pip.LATEST_PIP
    pip_path = get_pip.retrieve_pip(latest_pip)

    build_folder = paths.build_folder()
    lib_folder = os.path.join(build_folder, "lib")

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
            "--target",
            lib_folder,
        ]
        subprocess.run(pip_command)

        freeze_command = [
            python_path,
            pip_path,
            "freeze",
            "--path",
            lib_folder,
        ]

        freeze = subprocess.run(freeze_command, capture_output=True, text=True)

        (Path(lib_folder) / "requirements.txt").write_text(freeze.stdout)

        # Get the paths for modules that need to be copied
        resources = importlib_resources.files("ducktools.env")

        with importlib_resources.as_file(resources) as env_folder:
            main_app_path = env_folder / "__main__.py"
            platform_paths_path = env_folder / "platform_paths.py"
            bootstrap_path = env_folder / "scripts" / "bootstrap.py"

            print("Copying __main__.py into lib")
            shutil.copy(main_app_path, lib_folder)

            print("Copying platform paths")
            shutil.copy(platform_paths_path, os.path.join(build_folder, "platform_paths.py"))

            print("Copying bootstrap script")
            shutil.copy(bootstrap_path, os.path.join(build_folder, "__main__.py"))

        print("Creating ducktools-env.pyz")
        zipapp.create_archive(
            source=lib_folder,
            target=os.path.join(build_folder, "ducktools-env.pyz"),
            interpreter="/usr/bin/env python"
        )

        # Cleaning up lib folder
        shutil.rmtree(lib_folder)

        print("Copying pip.pyz into lib")
        shutil.copy(pip_path, build_folder)

        print("Writing version numbers")
        with open(os.path.join(build_folder, "pip.pyz.version"), 'w') as f:
            f.write(latest_pip.version_str)
        with open(os.path.join(build_folder, "ducktools-env.pyz.version"), 'w') as f:
            f.write(ducktools.env.__version__)

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
    try:
        path_base = sys.argv[1]
    except IndexError:
        path_base = str(Path(__file__).parents[1])

    build_zipapp(path_base)
