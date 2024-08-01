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
This module re-creates the ducktools-env zipapp
"""
import os
import os.path
import shutil
import subprocess
import sys
import zipapp

from glob import glob

from ducktools.env.scripts import get_pip, bootstrap
from ducktools.env import platform_paths, __main__ as main_app, _version, MINIMUM_PYTHON_STR


def build_zipapp(wheel_path):
    # Just use the existing Python to build
    python_path = sys.executable
    # pip is needed to build the zipapp
    paths = platform_paths.default_paths

    latest_pip = get_pip.LATEST_PIP
    pip_path = get_pip.retrieve_pip(latest_pip)

    build_folder = paths.build_folder()
    lib_folder = os.path.join(build_folder, "lib")

    build_folder_glob = os.path.normpath(
        os.path.join(build_folder, os.path.pardir, '*')
    )
    # Clear out old build folders
    for p in glob(build_folder_glob):
        if p != build_folder:
            shutil.rmtree(p)

    try:
        print("Downloading application modules")
        print(pip_path)
        # Pip install packages into build folder
        subprocess.run([
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
        ])

        print("Copying __main__.py into lib")
        shutil.copy(main_app.__file__, lib_folder)

        print("Creating ducktools.pyz")
        zipapp.create_archive(
            source=lib_folder,
            target=os.path.join(build_folder, "ducktools.pyz"),
        )

        # Cleaning up lib folder
        shutil.rmtree(lib_folder)

        print("Copying pip.pyz into lib")
        shutil.copy(pip_path, build_folder)

        print("Copying platform paths")
        shutil.copy(platform_paths.__file__, os.path.join(build_folder, "platform_paths.py"))

        print("Copying bootstrap script")
        shutil.copy(bootstrap.__file__, os.path.join(build_folder, "__main__.py"))

        print("Writing version numbers")
        with open(os.path.join(build_folder, "pip.pyz.version"), 'w') as f:
            f.write(latest_pip.version_str)
        with open(os.path.join(build_folder, "ducktools.pyz.version"), 'w') as f:
            f.write(_version.__version__)

        print("Creating zipapp")
        zipapp.create_archive(
            source=build_folder,
            target=os.path.join(os.getcwd(), "ducktools-env.pyz"),
            interpreter="/usr/bin/env python"
        )

    finally:
        pass  # clean up tempdir


if __name__ == "__main__":
    path_base = sys.argv[1]
    build_zipapp(path_base)