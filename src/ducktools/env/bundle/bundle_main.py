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

# This becomes the bundler bootstrap python script
import sys
import zipfile

from pathlib import Path


# Included in bundle
from _bootstrap import update_libraries, launch_script  # noqa


def main():
    # Get updated ducktools and pip
    update_libraries()

    # Get the path to this zipfile and the folder is is being run from
    zip_path = sys.argv[0]

    script_path = Path(zip_path).with_suffix(".py")
    script_name = script_path.name

    temp_path = script_path.with_suffix(".temp.py")

    i = 0
    while temp_path.exists():
        # Keep adding .temp.py until the path doesn't exist - up to a point
        temp_path = temp_path.with_suffix(".temp.py")
        i += 1
        if i > 5:
            raise FileExistsError(
                f"'{temp_path}' already exists, as did all the versions with fewer '.temp' segments"
            )

    working_dir = Path(zip_path).parent
    script_path = str(working_dir / script_name)

    try:
        with zipfile.ZipFile(zip_path) as zf:
            script_info = zf.getinfo(script_name)
            script_info.filename = temp_path.name
            # Extract the script file to the existing folder
            zf.extract(script_info, path=working_dir)
        launch_script(script_path, sys.argv[1:])
    finally:
        temp_path.unlink()


if __name__ == "__main__":
    main()
