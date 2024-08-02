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

from .. import MINIMUM_PYTHON_STR, bootstrap_requires
from ..platform_paths import default_paths
from ..scripts.get_pip import retrieve_pip
from ..scripts.create_zipapp import build_env_zipapp
from ..exceptions import ScriptNameClash

invalid_script_names = {
    "__main__.py",
    "_bootstrap.py",
    "_platform_paths.py",
    "_vendor.py",
}


def create_bundle(script_file, *, paths=default_paths):
    if script_file.endswith(".pyz") or script_file.endswith(".pyzw"):
        sys.stderr.write(
            "Bundles must be created from .py scripts not .pyz[w] archives\n"
        )

    if script_file in invalid_script_names:
        raise ScriptNameClash(
            f"Script {script_file!r} can't be bundled as the name clashes with "
            f"a script or library required for unbundling"
        )

    build_folder = paths.build_folder()

    print(f"Building bundle in {build_folder!r}")

    if not os.path.exists(paths.pip_zipapp):
        retrieve_pip()

    if not os.path.exists(paths.env_zipapp):
        build_env_zipapp()

    print("Copying libraries into build folder")
    # Copy pip and ducktools zipapps into folder
    shutil.copytree(paths.manager_folder, build_folder, dirs_exist_ok=True)

    resources = importlib_resources.files("ducktools.env")

    with importlib_resources.as_file(resources) as env_folder:
        platform_paths_path = env_folder / "platform_paths.py"
        bootstrap_path = env_folder / "scripts" / "bootstrap.py"
        main_zipapp_path = env_folder / "bundle" / "bundle_main.py"

        shutil.copy(platform_paths_path, os.path.join(build_folder, "_platform_paths.py"))
        shutil.copy(bootstrap_path, os.path.join(build_folder, "_bootstrap.py"))
        shutil.copy(main_zipapp_path, os.path.join(build_folder, "__main__.py"))

    print("Installing required unpacking libraries")
    vendor_folder = os.path.join(build_folder, "_vendor")

    pip_command = [
        sys.executable,
        paths.pip_zipapp,
        "--disable-pip-version-check",
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
        sys.executable,
        paths.pip_zipapp,
        "freeze",
        "--path",
        vendor_folder,
    ]

    freeze = subprocess.run(freeze_command, capture_output=True, text=True)

    (Path(vendor_folder) / "requirements.txt").write_text(freeze.stdout)

    print("Copying script to build folder and bundling")
    shutil.copy(script_file, os.path.join(build_folder, "ducktools_bundled_script.py"))

    archive_path = Path(script_file).with_suffix(".pyz")

    zipapp.create_archive(
        source=build_folder,
        target=Path(script_file).with_suffix(".pyz"),
        interpreter="/usr/bin/env python",
    )

    print(f"Bundled {script_file!r} as '{archive_path}'")
