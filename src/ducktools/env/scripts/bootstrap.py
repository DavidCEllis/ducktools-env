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
This script becomes the __main__.py script inside the ducktools-env zipapp.
"""

import os.path
import sys
import zipfile


from platform_paths import default_paths  # noqa

from _vendor.ducktools.lazyimporter import LazyImporter, FromImport, ModuleImport  # noqa

_laz = LazyImporter(
    [
        FromImport("_vendor.packaging.version", "Version"),
        ModuleImport("runpy"),
        ModuleImport("shutil"),
    ]
)


def is_outdated(installed_version: str | None, bundled_version: str) -> bool:
    # Shortcut for no version installed
    if installed_version is None:
        return True

    # Always consider dev versions outdated
    if "dev" in installed_version:
        return True

    # Shortcut for identical version string
    if installed_version == bundled_version:
        return False

    # Try to use tuples, fallback to packaging
    try:
        installed_info = tuple(int(segment) for segment in installed_version.split("."))
        bundled_info = tuple(int(segment) for segment in bundled_version.split("."))
    except (ValueError, TypeError):
        installed_info = _laz.Version(installed_version)
        bundled_info = _laz.Version(bundled_version)

    return installed_info < bundled_info


def update_libraries():
    archive_path = os.path.abspath(sys.argv[0])

    # Compare library versions to those in cache
    with zipfile.ZipFile(archive_path, "r") as zf:
        bundled_ducktools_ver = zipfile.Path(zf, "ducktools-env.pyz.version").read_text()
        bundled_pip_ver = zipfile.Path(zf, "pip.pyz.version").read_text()

        # Copy ducktools if outdated
        if is_outdated(default_paths.get_env_version(), bundled_ducktools_ver):
            sys.stderr.write("Installed ducktools is older than bundled, replacing.\n")
            zf.extract("ducktools-env.pyz", default_paths.manager_folder)
            zf.extract("ducktools-env.pyz.version", default_paths.manager_folder)

        # Copy pip if outdated
        if is_outdated(default_paths.get_pip_version(), bundled_pip_ver):
            sys.stderr.write("Installed pip is older than bundled, replacing.\n")
            zf.extract("pip.pyz", default_paths.manager_folder)
            zf.extract("pip.pyz.version", default_paths.manager_folder)


def launch_ducktools():
    _laz.runpy.run_path(default_paths.env_zipapp, run_name="__main__")


if __name__ == "__main__":
    update_libraries()
    launch_ducktools()
