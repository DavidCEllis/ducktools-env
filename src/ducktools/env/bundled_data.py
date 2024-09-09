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

"""
Handle extracting bundled data from archives or moving it for use as scripts
"""
import os
import os.path

from . import FOLDER_ENVVAR, DATA_BUNDLE_ENVVAR, LAUNCH_PATH_ENVVAR, LAUNCH_TYPE_ENVVAR
from ducktools.lazyimporter import LazyImporter, FromImport, ModuleImport
from ducktools.classbuilder.prefab import Prefab, attribute

_laz = LazyImporter(
    [
        FromImport("tempfile", "TemporaryDirectory"),
        ModuleImport("shutil"),
        ModuleImport("zipfile"),
    ],
)

# noinspection PyUnreachableCode
if False:
    from tempfile import TemporaryDirectory
    import shutil
    import zipfile

    _laz.TemporaryDirectory = TemporaryDirectory
    _laz.shutil = shutil
    _laz.zipfile = zipfile

    del TemporaryDirectory, shutil, zipfile


class BundledDataError(Exception):
    pass


def _get_bundle_data(base_data_path):
    ...


def _get_script_data(base_data_path):
    data_path = os.environ.get(DATA_BUNDLE_ENVVAR)
    if not data_path:
        raise BundledDataError("No data folder set")


class ScriptData(Prefab):
    launch_type: str
    launch_path: str
    data_dest_base: str
    data_bundle: str

    _temporary_directory: _laz.TemporaryDirectory | None = attribute(default=None, private=True)

    def _makedir_script(self, tempdir: _laz.TemporaryDirectory) -> None:
        # data-bundle is just a path
        _laz.shutil.copytree(self.data_bundle, tempdir.name)

    def _makedir_bundle(self, tempdir: _laz.TemporaryDirectory) -> None:
        # data_bundle is a path within a zipfile
        with zipfile.ZipFile(self.launch_path) as zf:
            extract_names = sorted(
                n for n in zf.namelist() if n.startswith(self.data_bundle)
            )
            zf.extractall(tempdir.name, members=extract_names)

    def __enter__(self):
        tempdir = _laz.TemporaryDirectory(dir=self.data_dest_base)
        try:
            if self.launch_type == "SCRIPT":
                self._makedir_script(tempdir)
            else:
                self._makedir_bundle(tempdir)
        except Exception:
            # Make sure the temporary directory is cleaned up if there is an error
            # This should happen by nature of falling out of scope, but be explicit
            tempdir.cleanup()
            raise

        self._temporary_directory = tempdir
        return self._temporary_directory.name

    def __exit__(self, exc_type, exc_val, exc_tb):
        if self._temporary_directory:
            self._temporary_directory.cleanup()


def get_data_folder():
    # get all relevant env variables
    ducktools_base_folder = os.environ.get(FOLDER_ENVVAR)
    launch_path = os.environ.get(LAUNCH_PATH_ENVVAR)
    launch_type = os.environ.get(LAUNCH_TYPE_ENVVAR)
    data_bundle = os.environ.get(DATA_BUNDLE_ENVVAR)

    env_pairs = [
        (FOLDER_ENVVAR, ducktools_base_folder),
        (LAUNCH_PATH_ENVVAR, launch_path),
        (LAUNCH_TYPE_ENVVAR, launch_type),
    ]

    for envkey, envvar in env_pairs:
        if envvar is None:
            raise BundledDataError(
                f"Environment variable {envkey!r} not found, "
                f"get_data_folder will only work with a bundled executable or script run"
            )

    if data_bundle is None:
        raise BundledDataError(f"No bundled data included with script {launch_path!r}")

    data_dest_base = os.path.join(ducktools_base_folder, "tempdata")

    # noinspection PyArgumentList
    return ScriptData(launch_type, launch_path, data_dest_base, data_bundle)
