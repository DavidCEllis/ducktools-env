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
import json
from datetime import timedelta
from pathlib import Path
import unittest.mock as mock

from ducktools.classbuilder.prefab import as_dict
from ducktools.env.config import Config


def test_lifetime_delta():
    config = Config(
        cache_lifetime=1.0
    )

    assert config.cache_lifetime_delta == timedelta(days=1)


class TestLoad:
    def test_load_basic(self):
        with (
            mock.patch("builtins.open") as open_mock,
            mock.patch("json.load") as json_load_mock,
        ):
            # Non-default values
            json_load_mock.return_value = {
                "cache_maxcount": 5,
                "cache_lifetime": 1.0,
                "use_uv": False,
                "uv_install_python": False,
            }
            confpath = "path/to/config"

            config = Config.load(confpath)

            open_mock.assert_called_once_with(confpath, 'r')
            json_load_mock.assert_called()

            # Confirm values loaded correctly
            assert config.cache_maxcount == 5
            assert config.cache_lifetime == 1.0
            assert config.use_uv is False
            assert config.uv_install_python is False

    def test_load_unknowns(self):
        with (
            mock.patch("builtins.open") as open_mock,
            mock.patch("json.load") as json_load_mock,
        ):
            # Non-default values
            json_load_mock.return_value = {
                "cache_maxcount": 5,
                "cache_lifetime": 1.0,
                "use_uv": False,
                "uv_install_python": False,
                "extra_invalid_value": True
            }

            config = Config.load("path/to/config")
            open_mock.assert_called()

            # Confirm values loaded correctly
            assert config.cache_maxcount == 5
            assert config.cache_lifetime == 1.0
            assert config.use_uv is False
            assert config.uv_install_python is False

            # Invalid value discarded
            assert not hasattr(config, "extra_invalid_value")

    def test_load_failure_decode(self):
        with (
            mock.patch("builtins.open"),
            mock.patch("json.load") as json_load_mock,
        ):
            json_load_mock.side_effect = json.JSONDecodeError("failed", "doc", 1)

            config = Config.load("path/to/config")

            # Assert equal to base config with no arguments
            assert config == Config()

    def test_load_failure_not_found(self):
        with (
            mock.patch("builtins.open") as open_mock,
        ):
            open_mock.side_effect = FileNotFoundError()

            config = Config.load("path/to/config")

            # Assert equal to base config with no arguments
            assert config == Config()


def test_save():
    with (
        mock.patch("os.makedirs") as makedirs_patch,
        mock.patch("builtins.open") as open_patch,
        mock.patch("json.dump") as dump_patch,
    ):
        file_mock = mock.MagicMock()
        open_patch.return_value.__enter__.return_value = file_mock

        config = Config()

        save_path = Path("path", "to", "config.json")

        config.save(str(save_path))

        makedirs_patch.assert_called_once_with(
            str(save_path.parent),
            exist_ok=True,
        )

        open_patch.assert_called_once_with(str(save_path), "w")

        dump_patch.assert_called_once_with(
            as_dict(config),
            file_mock,
            indent=2,
        )
