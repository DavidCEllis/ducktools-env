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
This script becomes the __main__.py script inside the ducktools.pyz zipapp.
"""
from __future__ import annotations

import os.path
import sys
import zipfile

# This file is moved and these imports created when bundling
from _platform_paths import ManagedPaths  # type: ignore
from _logger import log  # type: ignore

# This bootstrap script exists without ducktools.env and so needs a copy of project_name
PROJECT_NAME = "ducktools"

default_paths = ManagedPaths(PROJECT_NAME)

if sys.stderr:
    logger = sys.stderr
else:
    from io import StringIO
    logger = StringIO()


def is_outdated(installed_version: str | None, bundled_version: str) -> bool:
    # Shortcut for no version installed
    if installed_version is None:
        return True

    # Installed pre-releases should be replaced by equal version pre-releases
    # But not older releases
    if "dev" in installed_version:
        from _vendor.packaging.version import Version  # type: ignore
        installed_info = Version(installed_version)
        bundled_info = Version(bundled_version)

        return installed_info.release <= bundled_info.release

    # Shortcut for identical version string
    if installed_version == bundled_version:
        return False

    # Try to use tuples, fallback to packaging
    try:
        installed_info = tuple(int(segment) for segment in installed_version.split("."))
        bundled_info = tuple(int(segment) for segment in bundled_version.split("."))
    except (ValueError, TypeError):

        from _vendor.packaging.version import Version  # type: ignore
        installed_info = Version(installed_version)
        bundled_info = Version(bundled_version)

    return installed_info < bundled_info


def update_libraries():
    archive_path = os.path.abspath(sys.argv[0])

    # Compare library versions to those in cache
    with zipfile.ZipFile(archive_path, "r") as zf:
        bundled_ducktools_ver = zipfile.Path(zf, "ducktools-env.version").read_text()
        bundled_pip_ver = zipfile.Path(zf, "pip.pyz.version").read_text()

        # Copy ducktools if outdated
        if is_outdated(default_paths.get_env_version(), bundled_ducktools_ver):
            log("Installed ducktools is older than bundled, replacing.")
            extract_names = sorted(n for n in zf.namelist() if n.startswith("ducktools-env/"))
            zf.extractall(default_paths.manager_folder, members=extract_names)
            zf.extract("ducktools-env.version", default_paths.manager_folder)

        # Copy pip if outdated
        if is_outdated(default_paths.get_pip_version(), bundled_pip_ver):
            log("Installed pip is older than bundled, replacing.")
            zf.extract("pip.pyz", default_paths.manager_folder)
            zf.extract("pip.pyz.version", default_paths.manager_folder)


def launch_script(script_file, zipapp_path, args, lockdata=None):
    sys.path.insert(0, default_paths.env_folder)
    try:
        from ducktools.env.manager import Manager
        manager = Manager(project_name=PROJECT_NAME)
        manager.run_bundle(
            script_path=script_file,
            script_args=args,
            lockdata=lockdata,
            zipapp_path=zipapp_path,
        )
    finally:
        sys.path.pop(0)


def launch_ducktools():
    import runpy
    runpy.run_path(default_paths.env_folder, run_name="__main__")
