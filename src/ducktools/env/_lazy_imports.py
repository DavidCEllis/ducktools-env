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

from ducktools.lazyimporter import LazyImporter
from ducktools.lazyimporter.capture import capture_imports

__all__ = [
    # stdlib
    "hashlib",
    "json",
    "metadata",  # importlib.metadata
    "re",
    "shutil",
    "signal",
    "sql",
    "subprocess",
    "tempfile",
    "tomllib",
    "warnings",
    "zipfile",

    "TemporaryDirectory",
    "urlopen",

    # Packaging
    "Requirement",
    "InvalidRequirement",
    "SpecifierSet",
    "InvalidSpecifier",
    "Version",
    "InvalidVersion",

    # ducktools-pythonfinder
    "list_python_installs",
    "PythonInstall",
    "get_installed_uv_pythons",
]

laz = LazyImporter()


with capture_imports(laz):
    import hashlib
    import importlib.metadata as metadata
    import json
    import re
    import shutil
    import sqlite3 as sql
    import signal
    import subprocess
    import tempfile
    import warnings
    import zipfile

    if sys.version_info >= (3, 11):
        import tomllib as tomllib
    else:
        import tomli as tomllib

    from tempfile import TemporaryDirectory
    from urllib.request import urlopen

    from packaging.requirements import Requirement, InvalidRequirement
    from packaging.specifiers import SpecifierSet, InvalidSpecifier
    from packaging.version import Version, InvalidVersion

    from ducktools.pythonfinder import list_python_installs, PythonInstall
    from ducktools.pythonfinder.shared import get_uv_pythons as get_installed_uv_pythons
