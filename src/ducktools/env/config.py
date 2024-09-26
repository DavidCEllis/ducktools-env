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
User global configuration
"""
import os

from datetime import timedelta as _timedelta

from ducktools.classbuilder.prefab import Prefab, get_attributes, as_dict
from ._lazy_imports import laz as _laz


class Config(Prefab, kw_only=True):
    # Global settings for caches
    cache_maxcount: int = 10
    cache_lifetime: float = 14.0

    # Use uv and allow uv to auto install Python
    use_uv: bool = True
    uv_install_python: bool = True

    @property
    def cache_lifetime_delta(self) -> _timedelta:
        return _timedelta(days=self.cache_lifetime)

    @classmethod
    def load(cls, file_path: str):
        try:
            with open(file_path, 'r') as f:
                json_data = _laz.json.load(f)
        except (FileNotFoundError, _laz.json.JSONDecodeError):
            new_config = cls()
            # new_config.save(file_path)
            return new_config
        else:
            attribute_keys = {k for k, v in get_attributes(cls).items() if v.init}

            filtered_data = {
                k: v for k, v in json_data.items() if k in attribute_keys
            }

            # noinspection PyArgumentList
            return cls(**filtered_data)

    def save(self, file_path: str):
        os.makedirs(os.path.dirname(file_path), exist_ok=True)
        with open(file_path, "w") as f:
            _laz.json.dump(as_dict(self), f, indent=2)
