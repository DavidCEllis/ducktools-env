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

from ._version import __version__, __version_tuple__

PROJECT_NAME = "ducktools"
MINIMUM_PYTHON = (3, 8)
MINIMUM_PYTHON_STR = ".".join(str(v) for v in MINIMUM_PYTHON)

LAUNCH_TYPE_ENVVAR = "DUCKTOOLS_ENV_LAUNCH_TYPE"
LAUNCH_PATH_ENVVAR = "DUCKTOOLS_ENV_LAUNCH_PATH"
LAUNCH_ENVIRONMENT_ENVVAR = "DUCKTOOLS_ENV_LAUNCH_ENVIRONMENT"


bootstrap_requires = [
    "ducktools-lazyimporter>=0.5.1",
    "packaging>=23.2",
    "zipp>=3.16",
]

if sys.version_info < MINIMUM_PYTHON:
    v = sys.version_info
    major, minor = MINIMUM_PYTHON
    raise ImportError(
        f"Python {v.major}.{v.minor} is not supported by ducktools-env. "
        f"Python {major}.{minor} is the minimum required version."
    )
