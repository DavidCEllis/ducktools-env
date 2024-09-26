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
import sys
import os
import os.path
import shutil
import subprocess
import zipapp

from pathlib import Path

import importlib.resources
import importlib.metadata as metadata
from packaging.requirements import Requirement

import ducktools.env
from ducktools.env import MINIMUM_PYTHON_STR, bootstrap_requires
from ducktools.env.platform_paths import ManagedPaths


def build_env_folder(
        *,
        paths: ManagedPaths,
        install_base_command: list[str],
        clear_old_builds=True
) -> None:
    # Get the full requirements for ducktools-env
    deps = []
    reqs = metadata.requires("ducktools-env")  # Use hyphen name to be recognised by older python
    for req in reqs:
        req = Requirement(req)
        if not (req.marker and not req.marker.evaluate({"python_version": MINIMUM_PYTHON_STR})):
            deps.append(f"{req.name}{req.specifier}")

    with paths.build_folder() as build_folder:
        build_folder_path = Path(build_folder)

        if clear_old_builds:
            for p in build_folder_path.parent.glob("*"):
                if p != build_folder_path:
                    shutil.rmtree(p)

        print("Downloading application dependencies")

        # install packages into build folder
        install_command = [
            *install_base_command,
            "install",
            *deps,
            "--python-version",
            MINIMUM_PYTHON_STR,
            "--only-binary=:all:",
            "--no-compile",
            "--target",
            build_folder,
        ]

        subprocess.run(install_command)

        freeze_command = [
            *install_base_command,
            "freeze",
            "--path",
            build_folder,
        ]

        # don't include executable scripts
        shutil.rmtree(build_folder_path / "bin", ignore_errors=True)

        freeze = subprocess.run(freeze_command, capture_output=True, text=True)

        (build_folder_path / "requirements.txt").write_text(freeze.stdout)

        # Get the paths for modules that need to be copied
        resources = importlib.resources.files("ducktools.env")

        with importlib.resources.as_file(resources) as env_folder:
            print("Copying application into archive")
            ignore_compiled = shutil.ignore_patterns("__pycache__")
            shutil.copytree(
                env_folder,
                build_folder_path / "ducktools" / "env",
                ignore=ignore_compiled,
            )

            main_app_path = env_folder / "__main__.py"
            print("Copying __main__.py into lib")
            shutil.copy(main_app_path, build_folder_path)

        ver = metadata.version("ducktools-env")
        dist_info_foldername = f"ducktools_env-{ver}.dist-info"
        dist_info_dest = build_folder_path / dist_info_foldername
        dist_info_dest.mkdir()

        print(f"Copying {dist_info_foldername} into build folder")

        for f in metadata.files("ducktools-env"):
            # Skip direct_url file as it will point to local path
            if f.name == "direct_url.json":
                continue
            if str(f.parent) == dist_info_foldername:
                shutil.copy(f.locate(), dist_info_dest)

        print("Creating ducktools-env lib folder")
        shutil.rmtree(paths.env_folder, ignore_errors=True)
        shutil.copytree(
            build_folder,
            paths.env_folder,
        )

    print("Writing env version number")
    with open(paths.env_folder + ".version", 'w') as f:
        f.write(ducktools.env.__version__)


def build_zipapp(
        *,
        paths: ManagedPaths,
        install_base_command: list[str],
        clear_old_builds=True
) -> None:
    archive_name = "ducktools.pyz"

    with paths.build_folder() as build_folder:

        build_path = Path(build_folder)

        if clear_old_builds:
            for p in build_path.parent.glob("*"):
                if p != build_path:
                    shutil.rmtree(p)

        # UV should not be bundled - binary is not cross platform
        uv_base_exe = "uv.exe" if sys.platform == "win32" else "uv"
        ignore_patterns = shutil.ignore_patterns(
            "__pycache__",
            uv_base_exe,
            f"{uv_base_exe}.version"
        )

        print("Copying pip.pyz and ducktools-env")
        shutil.copytree(paths.manager_folder, build_folder, ignore=ignore_patterns, dirs_exist_ok=True)

        # Get the paths for modules that need to be copied
        resources = importlib.resources.files("ducktools.env")

        with importlib.resources.as_file(resources) as env_folder:
            platform_paths_path = env_folder / "platform_paths.py"
            logging_path = env_folder / "_logger.py"
            bootstrap_path = env_folder / "bootstrapping" / "bootstrap.py"
            version_check_path = env_folder / "bootstrapping" / "version_check.py"

            main_zipapp_path = env_folder / "bootstrapping" / "zipapp_main.py"

            print("Copying platform paths")
            shutil.copy(platform_paths_path, build_path / "_platform_paths.py")

            print("Copying bootstrap script")
            shutil.copy(bootstrap_path, build_path / "_bootstrap.py")

            print("Copying version check script")
            shutil.copy(version_check_path, build_path / "_version_check.py")

            print("Copying logger script")
            shutil.copy(logging_path, build_path / "_logger.py")

            print("Copying __main__ script")
            shutil.copy(main_zipapp_path, build_path / "__main__.py")

        print("Installing bootstrap requirements")
        vendor_folder = os.path.join(build_folder, "_vendor")

        pip_command = [
            *install_base_command,
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
            *install_base_command,
            "freeze",
            "--path",
            vendor_folder,
        ]

        freeze = subprocess.run(freeze_command, capture_output=True, text=True)

        (Path(vendor_folder) / "requirements.txt").write_text(freeze.stdout)

        dist_folder = Path(os.getcwd(), "dist")
        dist_folder.mkdir(exist_ok=True)

        print(f"Creating {archive_name}")
        zipapp.create_archive(
            source=build_folder,
            target=dist_folder / archive_name,
            interpreter="/usr/bin/env python"
        )
