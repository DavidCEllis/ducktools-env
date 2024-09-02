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

import unittest.mock as mock

import pytest

from ducktools.env.catalogue import BaseCatalogue, TempCatalogue
from ducktools.env.catalogue import _laz  # noqa


@pytest.fixture
def mock_save():
    # Mock the .save() function from BaseCatalogue
    with mock.patch.object(BaseCatalogue, "save") as save_func:
        yield save_func


@pytest.fixture
def mock_subprocess():
    # Subprocess module lives in the _laz object
    with mock.patch.object(_laz, "subprocess") as subprocess_obj:
        yield subprocess_obj


@pytest.mark.usefixtures("mock_save")
class TempCatalogueTests:
    ...
