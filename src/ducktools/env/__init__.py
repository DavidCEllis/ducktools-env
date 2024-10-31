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

from ._version import (
    __version__ as __version__,
    __version_tuple__ as __version_tuple__
)


MINIMUM_PYTHON = (3, 10)
MINIMUM_PYTHON_STR = ".".join(str(v) for v in MINIMUM_PYTHON)


PROJECT_NAME = "ducktools"
APP_COMMAND = "ducktools-env"

FOLDER_ENVVAR = "DUCKTOOLS_ENV_FOLDER"
LAUNCH_TYPE_ENVVAR = "DUCKTOOLS_ENV_LAUNCH_TYPE"
LAUNCH_PATH_ENVVAR = "DUCKTOOLS_ENV_LAUNCH_PATH"
LAUNCH_ENVIRONMENT_ENVVAR = "DUCKTOOLS_ENV_LAUNCH_ENVIRONMENT"
DATA_BUNDLE_ENVVAR = "DUCKTOOLS_ENV_BUNDLED_DATA"

DATA_BUNDLE_FOLDER = "bundledata"


bootstrap_requires = [
    "packaging>=23.2",
]
