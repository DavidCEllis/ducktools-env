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

# /// script
# requires-python = ">=3.11"
#
# [tool.ducktools.env]
# include.data = ["./"]
# ///
import sys
import os
import os.path

from pathlib import Path

DUCKTOOLS_FOLDER = os.environ.get("DUCKTOOLS_ENV_FOLDER")
LAUNCH_TYPE = os.environ.get("DUCKTOOLS_ENV_LAUNCH_TYPE")
LAUNCH_PATH = os.environ.get("DUCKTOOLS_ENV_LAUNCH_PATH")
LAUNCH_ENVIRONMENT = os.environ.get("DUCKTOOLS_ENV_LAUNCH_ENVIRONMENT")
DATA_FILES = os.environ.get("DUCKTOOLS_ENV_BUNDLED_DATA")


# Hack to get ducktools in PATH so it is importable in the venv
extra_path = os.path.join(DUCKTOOLS_FOLDER, "lib", "ducktools-env")
sys.path.insert(0, extra_path)

print(f"{DUCKTOOLS_FOLDER=}")
print(f"{LAUNCH_TYPE=}")
print(f"{LAUNCH_PATH=}")
print(f"{LAUNCH_ENVIRONMENT=}")
print(f"{DATA_FILES=}")

from ducktools.env.bundled_data import get_data_folder

with get_data_folder() as fld:
    for f in Path(fld).rglob("*"):
        print(f)
