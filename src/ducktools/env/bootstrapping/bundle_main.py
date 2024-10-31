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

# Suppress ruff error for imports not at the top of the file,
# version check needs to come first.
# ruff: noqa: E402

# This becomes the bundler bootstrap python script
import sys

from _version_check import version_check  # type: ignore
version_check()


import zipfile
from pathlib import Path

# Included in bundle
from _bootstrap import update_libraries, launch_script  # type: ignore


def main(script_name):
    # Get updated ducktools and pip
    update_libraries()

    # Get the path to this zipfile and the folder is is being run from
    zip_path = sys.argv[0]

    script_dest = Path(zip_path).with_suffix(".py")

    i = 0
    while script_dest.exists():
        # Keep adding .temp.py until the path doesn't exist - up to a point
        script_dest = script_dest.with_suffix(".temp.py")
        i += 1
        if i > 5:
            raise FileExistsError(
                f"'{script_dest}' already exists, as did all the versions with fewer '.temp' segments"
            )

    working_dir = Path(zip_path).parent

    try:
        with zipfile.ZipFile(zip_path) as zf:
            script_info = zf.getinfo(script_name)
            script_info.filename = script_dest.name

            # Get lockfile if it exists
            lock_name = f"{script_name}.lock"
            try:
                lockdata = zipfile.Path(zf, lock_name).read_text()
            except FileNotFoundError:
                # No lockfile
                lockdata = None
            
            # Extract the script file to the existing folder
            zf.extract(script_info, path=working_dir)

        launch_script(
            script_file=str(script_dest),
            zipapp_path=zip_path,
            args=sys.argv[1:],
            lockdata=lockdata,
        )
    finally:
        script_dest.unlink()

# BUNDLE CODE TO EXECUTE SCRIPT FOLLOWS
