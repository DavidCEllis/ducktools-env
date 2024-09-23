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
import sys

MINIMUM_PYTHON = (3, 10)
MINIMUM_PYTHON_STR = ".".join(str(v) for v in MINIMUM_PYTHON)


def version_check():
    v = sys.version_info
    if v < MINIMUM_PYTHON:
        major, minor = MINIMUM_PYTHON
        header = "The Python version used to unpack this zipapp is outdated."
        message = (
            f"Python {v.major}.{v.minor} is not supported. "
            f"Python {major}.{minor} is the minimum required version."
        )
        if sys.platform in {"win32", "darwin"}:
            message += " You can get the latest Python from: https://www.python.org/downloads/"

        if sys.stdout:
            print(header)
            print(message)
        else:
            from tkinter import messagebox, Tk
            root = Tk()
            root.withdraw()
            try:
                messagebox.showerror(
                    parent=root,
                    title=header,
                    message=message,
                )
            finally:
                root.destroy()

        sys.exit()
