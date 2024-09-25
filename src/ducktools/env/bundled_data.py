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
Handle extracting bundled data from archives or moving it for use as scripts
"""
from __future__ import annotations

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

from ducktools.classbuilder.prefab import Prefab, attribute

from ._lazy_imports import laz as _laz


class BundledDataError(Exception):
    pass


class ScriptData(Prefab):
    """
    Context manager that gives a folder containing the data associated with
    the running script.

    This handles the differences between being run by a script via
    the 'run' command and through running a bundle made by ducktools-env.

    :raises FileNotFoundError: If the data source does not exist
    :return: String path to the data folder when used as a context manager
    """

    launch_type: str
    launch_path: str
    data_dest_base: str
    data_bundle: str

    _temporary_directory: _laz.TemporaryDirectory | None = attribute(default=None, private=True)  # type: ignore

    def _makedir_script(self, tempdir: _laz.TemporaryDirectory) -> None:  # type: ignore
        # The data is in folders relative to the script path
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

    def _makedir_bundle(self, tempdir: _laz.TemporaryDirectory) -> None:  # type: ignore
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
        self._temporary_directory = None


def get_data_folder():
    """
    Copy data required by the script into a temporary folder and yield the path
    to the temporary folder that contains the data.

    :raises BundledDataError: If no data bundle is included with the script
    :raises BundledDataError: If one of the required environment variables is not present
                              This *should* only happen if used outside of a ducktools.env script run
    :return: The scriptdata object context manager, this should be used as a context manager
             in order to obtain the path to the temporary data folder.
    """
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
