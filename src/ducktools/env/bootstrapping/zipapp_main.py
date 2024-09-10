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
This is the bootstrapping script for the ducktools.pyz bundle itself
"""
import sys

from _check_outdated_python import python_version_outdated  # type: ignore

message = python_version_outdated()
if message:
    print("The Python version used to unpack this bundle is outdated.")
    print(message)
    if sys.platform in {"win32", "darwin"}:
        print("You can get the latest Python from: https://www.python.org/downloads/")
    input("Press any key to close")
    sys.exit()
del message

from _bootstrap import update_libraries, launch_ducktools  # noqa

if __name__ == "__main__":
    update_libraries()
    launch_ducktools()
