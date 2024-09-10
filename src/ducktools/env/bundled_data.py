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
import sys
import os
import os.path

from . import (
    FOLDER_ENVVAR,
    DATA_BUNDLE_ENVVAR,
    DATA_BUNDLE_FOLDER,
    LAUNCH_PATH_ENVVAR,
    LAUNCH_TYPE_ENVVAR
)
from ducktools.lazyimporter import LazyImporter, FromImport, ModuleImport
from ducktools.classbuilder.prefab import Prefab, attribute

_laz = LazyImporter(
    [
        FromImport("tempfile", "TemporaryDirectory"),
        ModuleImport("shutil"),
        ModuleImport("zipfile"),
    ],
)

# Autocomplete helpers - type checkers may complain
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


class ScriptData(Prefab):
    launch_type: str
    launch_path: str
    data_dest_base: str
    data_bundle: str

    _temporary_directory: _laz.TemporaryDirectory | None = attribute(default=None, private=True)

    def _makedir_script(self, tempdir: _laz.TemporaryDirectory) -> None:
        split_char = ";" if sys.platform == "win32" else ":"
        for p in self.data_bundle.split(split_char):
            base_path = os.path.dirname(self.launch_path)
            resolved_path = os.path.join(base_path, p)

            if os.path.isfile(resolved_path):
                _laz.shutil.copy(resolved_path, tempdir.name)
            elif os.path.isdir(resolved_path):
                dest = os.path.join(
                    tempdir.name,
                    os.path.basename(os.path.normpath(resolved_path))
                )
                _laz.shutil.copytree(resolved_path, dest)
            else:
                raise FileNotFoundError(f"Could not find data file {p!r}")

    def _makedir_bundle(self, tempdir: _laz.TemporaryDirectory) -> None:
        # data_bundle is a path within a zipfile
        with _laz.zipfile.ZipFile(self.launch_path) as zf:
            extract_names = sorted(
                n for n in zf.namelist()
                if n.startswith(self.data_bundle)
            )
            zf.extractall(tempdir.name, members=extract_names)

    def __enter__(self):
        os.makedirs(self.data_dest_base, exist_ok=True)
        tempdir = _laz.TemporaryDirectory(dir=self.data_dest_base)
        try:
            if self.launch_type == "SCRIPT":
                self._makedir_script(tempdir)
                temp_path = tempdir.name
            else:
                self._makedir_bundle(tempdir)
                temp_path = os.path.join(tempdir.name, DATA_BUNDLE_FOLDER)
        except Exception:
            # Make sure the temporary directory is cleaned up if there is an error
            # This should happen by nature of falling out of scope, but be explicit
            tempdir.cleanup()
            raise

        self._temporary_directory = tempdir
        return temp_path

    def __exit__(self, exc_type, exc_val, exc_tb):
        if self._temporary_directory:
            self._temporary_directory.cleanup()


def get_data_folder():
    # get all relevant env variables
    ducktools_base_folder = os.environ.get(FOLDER_ENVVAR)
    launch_path = os.environ.get(LAUNCH_PATH_ENVVAR)
    launch_type = os.environ.get(LAUNCH_TYPE_ENVVAR)
    data_bundle = os.environ.get(DATA_BUNDLE_ENVVAR)

    if data_bundle is None:
        raise BundledDataError(f"No bundled data included with script {launch_path!r}")

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

    data_dest_base = os.path.join(ducktools_base_folder, "tempdata")

    # noinspection PyArgumentList
    return ScriptData(launch_type, launch_path, data_dest_base, data_bundle)
