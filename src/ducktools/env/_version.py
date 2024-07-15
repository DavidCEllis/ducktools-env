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

import os.path

# noinspection PyUnresolvedReferences
__all__ = ["__version__"]


def __getattr__(name):
    if name == "__version__":
        # setuptools-scm should write a _version.txt file
        # if for whatever reason this isn't found, fall back to importlib-metadata

        fld = os.path.split(__file__)[0]
        version_file = os.path.join(fld, "_version.txt")
        try:
            with open(version_file, 'r') as version_txt:
                v = version_txt.read()
        except FileNotFoundError:
            from importlib import metadata
            v = metadata.version("ducktools-env")

        globals()["__version__"] = v
        return v


def __dir__():
    return ["__version__"]
