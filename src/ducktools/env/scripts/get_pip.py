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

The pip zipapp will be included in ducktools.pyz builds so this should only be needed
when building ducktools.pyz or if ducktools-env has been installed via pip.
"""
import os
import os.path

from ducktools.classbuilder.prefab import prefab

from ..platform_paths import ManagedPaths
from .._logger import log
from ..exceptions import InvalidPipDownload
from .._lazy_imports import laz as _laz

BASE_URL = "https://bootstrap.pypa.io/pip"


@prefab(frozen=True)
class PipZipapp:
    version_str: str
    sha3_256: str
    source_url: str

    @property
    def full_url(self):
        return f"{BASE_URL}/{self.source_url}"

    @property
    def version_tuple(self):
        return tuple(int(segment) for segment in self.version_str.split("."))

    @property
    def as_version(self):
        return _laz.Version(self.version_str)


# This is mostly kept for testing.
PREVIOUS_PIP = PipZipapp(
    version_str="24.2",
    sha3_256="8dc4860613c47cb2e5e55c7e1ecf4046abe18edca083073d51f1720011bed6ea",
    source_url="zipapp/pip-24.2.pyz",
)

LATEST_PIP = PipZipapp(
    version_str="24.3.1",
    sha3_256="6dd95ab685d00abada578f2744f2b235faf5876d3f3468f0756e2b78bce050f1",
    source_url="zipapp/pip-24.3.1.pyz"
)


def is_pip_outdated(
    paths: ManagedPaths,
    latest_version: PipZipapp = LATEST_PIP
):
    pip_version = paths.get_pip_version()

    if pip_version is None:
        return True

    try:
        installed_info = tuple(int(segment) for segment in pip_version.split("."))
        latest_info = latest_version.version_tuple
    except (ValueError, TypeError):
        # possible pre/post release versions - use packaging
        installed_info = _laz.Version(pip_version)
        latest_info = latest_version.as_version

    return installed_info < latest_info


def download_pip(
    pip_destination: str,
    latest_version: PipZipapp = LATEST_PIP
):

    url = latest_version.full_url

    # Actual download
    with _laz.urlopen(url) as f:
        data = f.read()

    # Check hash matches
    if _laz.hashlib.sha3_256(data).hexdigest() != latest_version.sha3_256:
        raise InvalidPipDownload(
            "The checksum of the downloaded PIP binary did not match the expected value."
        )

    # Make directory if it does not exist
    os.makedirs(os.path.dirname(pip_destination), exist_ok=True)

    with open(pip_destination, 'wb') as f:
        f.write(data)

    with open(f"{pip_destination}.version", 'w') as f:
        f.write(".".join(str(item) for item in latest_version.version_tuple))


def retrieve_pip(
    paths: ManagedPaths,
    latest_version: PipZipapp = LATEST_PIP,
) -> str:
    """
    If pip.pyz is not installed, download it and place it in the cache
    return the path to the .pyz

    :param paths:
    :param latest_version:
    :return: path to pip.pyz
    """

    if is_pip_outdated(paths, latest_version=latest_version):
        log("Downloading PIP")
        download_pip(paths.pip_zipapp, latest_version=latest_version)

        log(f"Pip zipapp installed at {paths.pip_zipapp!r}")

    return paths.pip_zipapp
