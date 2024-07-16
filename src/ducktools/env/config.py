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
import sys
import os

from datetime import timedelta as _timedelta

from ducktools.lazyimporter import LazyImporter, ModuleImport
from ducktools.classbuilder.prefab import Prefab, get_attributes, as_dict

_laz = LazyImporter(
    [
        ModuleImport("json"),
    ]
)


def log(message):
    sys.stderr.write(message)
    sys.stderr.write("\n")


class Config(Prefab, kw_only=True):
    # Global settings for caches
    cache_maxcount: int = 10
    cache_lifetime: float = 1.0

    applications_expire: bool = False
    applications_lifetime: float = 14.0

    def cache_lifetime_delta(self) -> _timedelta:
        return _timedelta(days=self.cache_lifetime)

    @classmethod
    def load(cls, file_path: str):
        try:
            with open(file_path, 'r') as f:
                json_data = _laz.json.load(f)
        except (FileNotFoundError, _laz.json.JSONDecodeError):
            return cls()
        else:
            attribute_keys = {k for k, v in get_attributes(cls).items() if v.init}
            valid_keys = json_data.keys() & attribute_keys

            # noinspection PyArgumentList
            return cls(**valid_keys)

    def save(self, file_path: str):
        os.makedirs(os.path.split(file_path)[0], exist_ok=True)
        with open(file_path, "w") as f:
            _laz.json.dump(self, f, default=as_dict)
