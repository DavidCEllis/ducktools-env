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
import os
import unittest.mock as mock
from pathlib import Path

import pytest
from packaging.version import Version

import ducktools.env.scripts.get_pip as get_pip
from ducktools.env._lazy_imports import laz
from ducktools.env.exceptions import InvalidPipDownload
from ducktools.env.platform_paths import ManagedPaths

PIP_ZIPAPP = Path(__file__).parent / "data/pip-24.2.pyz"


def test_latest_pip():
    pip_ver = get_pip.PipZipapp(
        version_str="24.2",
        sha3_256="8dc4860613c47cb2e5e55c7e1ecf4046abe18edca083073d51f1720011bed6ea",
        source_url="zipapp/pip-24.2.pyz",
    )

    assert pip_ver.version_tuple == (24, 2)
    assert pip_ver.as_version == Version("24.2")

    assert pip_ver.full_url == "https://bootstrap.pypa.io/pip/zipapp/pip-24.2.pyz"


def test_is_pip_outdated():
    pip_ver = get_pip.PipZipapp(
        version_str="24.2",
        sha3_256="8dc4860613c47cb2e5e55c7e1ecf4046abe18edca083073d51f1720011bed6ea",
        source_url="zipapp/pip-24.2.pyz",
    )

    paths = ManagedPaths("ducktools")

    with mock.patch.object(paths, "get_pip_version") as get_pip_ver:
        get_pip_ver.return_value = "24.2"
        outdated_check = get_pip.is_pip_outdated(paths, pip_ver)
        assert outdated_check is False

        get_pip_ver.return_value = "24.1"
        outdated_check = get_pip.is_pip_outdated(paths, pip_ver)
        assert outdated_check is True

        get_pip_ver.return_value = None
        outdated_check = get_pip.is_pip_outdated(paths, pip_ver)
        assert outdated_check is True

        get_pip_ver.return_value = "24.2b1"
        outdated_check = get_pip.is_pip_outdated(paths, pip_ver)
        assert outdated_check is True


def test_download_pip():
    pip_ver = get_pip.PipZipapp(
        version_str="24.2",
        sha3_256="8dc4860613c47cb2e5e55c7e1ecf4046abe18edca083073d51f1720011bed6ea",
        source_url="zipapp/pip-24.2.pyz",
    )

    mock_urlopen = mock.mock_open(read_data=b"data")

    with (
        mock.patch.object(laz, "urlopen", mock_urlopen),
        mock.patch("builtins.open") as mock_open,
        mock.patch("hashlib.sha3_256") as sha_mock,
        mock.patch("os.makedirs") as mkdir_mock,
    ):
        hexmock = mock.MagicMock()
        hexmock.hexdigest.return_value = "8dc4860613c47cb2e5e55c7e1ecf4046abe18edca083073d51f1720011bed6ea"

        sha_mock.return_value = hexmock

        file_mock = mock.MagicMock()
        mock_open.return_value.__enter__.return_value = file_mock

        pip_destination = "./data/pip-download.pyz"

        get_pip.download_pip(pip_destination, pip_ver)

        sha_mock.assert_called_with(b"data")
        mkdir_mock.assert_called_with(os.path.dirname(pip_destination), exist_ok=True)

        mock_open.assert_any_call(pip_destination, "wb")
        mock_open.assert_any_call(f"{pip_destination}.version", "w")

        file_mock.write.assert_any_call(b"data")
        file_mock.write.assert_any_call("24.2")

        hexmock.hexdigest.return_value = "failure"

        with pytest.raises(InvalidPipDownload):
            get_pip.download_pip(pip_destination, pip_ver)


def test_retrieve_pip():
    with (
        mock.patch("ducktools.env.scripts.get_pip.is_pip_outdated") as outdated_check,
        mock.patch("ducktools.env.scripts.get_pip.download_pip") as download_cmd,
        mock.patch("ducktools.env.scripts.get_pip.log") as logger,
    ):
        pip_ver = get_pip.PipZipapp(
            version_str="24.2",
            sha3_256="8dc4860613c47cb2e5e55c7e1ecf4046abe18edca083073d51f1720011bed6ea",
            source_url="zipapp/pip-24.2.pyz",
        )

        # Pip not outdated - check no download
        outdated_check.return_value = False
        paths = ManagedPaths("ducktools")

        get_pip.retrieve_pip(paths, latest_version=pip_ver)

        outdated_check.assert_called_once_with(paths, latest_version=pip_ver)
        outdated_check.reset_mock()

        logger.assert_not_called()
        download_cmd.assert_not_called()

        # If pip is outdated - check download command runs
        outdated_check.return_value = True
        get_pip.retrieve_pip(paths, latest_version=pip_ver)
        outdated_check.assert_called_once_with(paths, latest_version=pip_ver)

        logger.assert_called()  # Not going to care about the log messages

        download_cmd.assert_called_once_with(paths.pip_zipapp, latest_version=pip_ver)
