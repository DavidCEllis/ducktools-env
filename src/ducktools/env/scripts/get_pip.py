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
This module handles downloading and installing the `pip.pyz` zipapp if it is outdated
or not installed.

The pip zipapp will be included in ducktools-env.pyz builds so this should only be needed
when building ducktools-env.pyz or if ducktools-env has been installed via pip.
"""

from __future__ import annotations

import os
import os.path

from ducktools.classbuilder.prefab import prefab

from ducktools.env import platform_paths
from ducktools.env.exceptions import InvalidPipDownload


BASE_URL = "https://bootstrap.pypa.io/pip"


@prefab(frozen=True)
class PipZipapp:
    version_tuple: tuple[int, ...]
    sha3_256: str
    source_url: str

    @property
    def full_url(self):
        return f"{BASE_URL}/{self.source_url}"

    @property
    def version_str(self):
        return ".".join(str(i) for i in self.version_tuple)


# This is mostly kept for testing.
PREVIOUS_PIP = PipZipapp(
    version_tuple=(24, 1),
    sha3_256="f4c4d76e70498762832a842d5b55e9d8c09b6d6607b30b5f4eb08e68dfc57077",
    source_url="zipapp/pip-24.1.pyz"
)

LATEST_PIP = PipZipapp(
    version_tuple=(24, 2),
    sha3_256="8dc4860613c47cb2e5e55c7e1ecf4046abe18edca083073d51f1720011bed6ea",
    source_url="zipapp/pip-24.2.pyz",
)


def is_pip_outdated(
        paths: platform_paths.ManagedPaths,
        latest_version: PipZipapp = LATEST_PIP
):
    pip_version = paths.get_pip_version()

    return pip_version < latest_version.version_tuple


def download_pip(
        pip_destination: str,
        latest_version: PipZipapp = LATEST_PIP
):
    import urllib.request
    import hashlib

    url = latest_version.full_url

    # Actual download
    with urllib.request.urlopen(url) as f:
        data = f.read()

    # Check hash matches
    if hashlib.sha3_256(data).hexdigest() != latest_version.sha3_256:
        raise InvalidPipDownload(
            "The checksum of the downloaded PIP binary did not match the expected value."
        )

    # Make directory if it does not exist
    os.makedirs(os.path.dirname(pip_destination), exist_ok=True)

    with open(pip_destination, 'wb') as f:
        f.write(data)

    with open(f"{pip_destination}.version", 'w') as f:
        f.write(".".join(str(item) for item in latest_version.version_tuple))


def retrieve_pip(latest_version: PipZipapp = LATEST_PIP) -> str:
    """
    If pip.pyz is not installed, download it and place it in the cache
    return the path to the .pyz

    :param latest_version:
    :return: path to pip.pyz
    """
    paths = platform_paths.default_paths

    if is_pip_outdated(paths, latest_version=latest_version):
        print("Downloading PIP")
        download_pip(paths.pip_zipapp, latest_version=latest_version)

        print(f"Pip zipapp installed at {paths.pip_zipapp!r}")
    else:
        print("Pip is already up to date")

    return paths.pip_zipapp


if __name__ == "__main__":
    retrieve_pip()
