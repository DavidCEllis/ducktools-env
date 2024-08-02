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
    script_name = "_bundled_script.py"

    # Get updated ducktools and pip
    update_libraries()

    # Get the path to this zipfile and the folder is is being run from
    zip_path = sys.argv[0]
    working_dir = Path(zip_path).parent
    script_path = str(working_dir / script_name)

    try:
        with zipfile.ZipFile(zip_path) as zf:
            # Extract the script file to the existing folder
            zf.extract(script_name, path=working_dir)
        launch_script(script_path, sys.argv[1:])
    finally:
        Path(script_path).unlink()


if __name__ == "__main__":
    main()
