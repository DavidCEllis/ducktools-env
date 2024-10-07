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
# Get python install has so many branches I wanted a separate test
import sys

from pathlib import Path

import pytest

from ducktools.env.environment_specs import EnvironmentSpec
from ducktools.env.exceptions import PythonVersionNotFound
from ducktools.env.config import Config
from ducktools.env.manager import Manager


class TestGetPythonInstall:
    example_paths = Path(__file__).parent / "example_scripts"

    def test_finds_python(self):
        config = Config(use_uv=False, uv_install_python=False)
        manager = Manager(project_name="ducktools-testing", config=config)

        script = str(self.example_paths / "pep_723_example.py")
        spec = EnvironmentSpec.from_script(script)

        # Patch the spec version to match this python install
        this_python = ".".join(str(i) for i in sys.version_info[:3])
        spec.details.requires_python = f"=={this_python}"

        inst = manager._get_python_install(spec=spec)

        assert inst.executable == sys.executable

    def test_no_python(self):
        config = Config(use_uv=False, uv_install_python=False)

        manager = Manager(project_name="ducktools-testing", config=config)
        script = str(self.example_paths / "pep_723_example.py")
        spec = EnvironmentSpec.from_script(script)

        # Patch the spec version to match this python install
        this_python = ".".join(str(i) for i in sys.version_info[:3])
        spec.details.requires_python = f">{this_python}"

        with pytest.raises(PythonVersionNotFound):
            manager._get_python_install(spec=spec)

