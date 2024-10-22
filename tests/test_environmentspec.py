# DuckTools-EnvMan
# Copyright (C) 2024 David C Ellis
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Lesser General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Lesser General Public License for more details.
#
# You should have received a copy of the GNU Lesser General Public License
# along with this program.  If not, see <https://www.gnu.org/licenses/>.
from __future__ import annotations

import unittest.mock as mock
from hashlib import sha3_256
from pathlib import Path

import pytest
from packaging.requirements import Requirement
from packaging.specifiers import SpecifierSet
from packaging.version import Version

import ducktools.env.environment_specs as env_specs
from ducktools.classbuilder.prefab import attribute, prefab
from ducktools.env.environment_specs import EnvironmentSpec
from ducktools.env.exceptions import ApplicationError
from ducktools.scriptmetadata import MetadataWarning

MOCK_RUN_STDOUT = "<MOCK DATA>"

EXAMPLES_FOLDER = Path(__file__).parent / "example_scripts"


@pytest.fixture
def subprocess_run_mock():
    with mock.patch("subprocess.run") as run_mock:
        run_return_mock = mock.MagicMock()
        run_return_mock.stdout = MOCK_RUN_STDOUT
        run_mock.return_value = run_return_mock

        yield run_mock


@prefab
class DataSet:
    raw_spec: str
    requires_python: str | None = None
    dependencies: list[str] = attribute(default_factory=list)
    extras: dict = attribute(default_factory=dict)


envs = [
    DataSet(
        raw_spec="",
    ),
    DataSet(
        raw_spec=("requires-python = '>=3.10'\n" "dependencies = []\n"),
        requires_python=">=3.10",
    ),
    DataSet(
        raw_spec=(
            "requires-python = '>=3.11'\n" "dependencies = ['ducktools-env>=0.1.0']\n"
        ),
        requires_python=">=3.11",
        dependencies=["ducktools-env>=0.1.0"],
    ),
]


class TestExampleSpecs:
    def test_cowsay_script(self):
        cowsay_script_path = EXAMPLES_FOLDER / "cowsay_ex.py"
        cowsay_lock_path = EXAMPLES_FOLDER / "cowsay_ex.py.lock"
        
        spec = EnvironmentSpec.from_script(cowsay_script_path)

        assert spec.details.requires_python == ">=3.8.0"
        assert spec.details.dependencies == ["cowsay"]
        assert spec.details.tool_table == {}

        assert spec.lockdata == cowsay_lock_path.read_text()

        assert spec.details.app is None


    def test_print_envvars_script(self):
        envvar_script_path = EXAMPLES_FOLDER / "print_environment_variables.py"

        spec = EnvironmentSpec.from_script(envvar_script_path)

        assert spec.details.requires_python == ">=3.10"
        assert spec.details.dependencies == []

        assert spec.details.data_sources == ["./"]
        assert spec.details.license == ["../LICENSE"]

        assert spec.lockdata is None

        assert spec.details.app is None


    def test_invalid_app(self):
        invalid_script_path = EXAMPLES_FOLDER / "invalid_app.py"

        spec = EnvironmentSpec.from_script(invalid_script_path)

        with pytest.raises(ApplicationError):
            _ = spec.details.app

    def test_cowsay_app(self):
        cowsay_app_path = EXAMPLES_FOLDER / "cowsay_app.py"
        cowsay_lock_path = EXAMPLES_FOLDER / "cowsay_app.py.lock"

        spec = EnvironmentSpec.from_script(cowsay_app_path)

        assert spec.details.requires_python == ">=3.8.0"
        assert spec.details.dependencies == ["cowsay"]

        cowsay_lockdata = cowsay_lock_path.read_text()
        assert spec.lockdata == cowsay_lockdata
        assert spec.lock_hash == sha3_256(
            cowsay_lockdata.encode("utf8")
        ).hexdigest()

        assert spec.details.data_sources is None

        assert spec.details.app.owner == "ducktools_testing"
        assert spec.details.app.appname == "cowsay_example"
        assert spec.details.app.version == "v0.1.0"
        assert spec.details.app.appkey == "ducktools_testing/cowsay_example"
        assert spec.details.app.version_spec == Version("0.1.0")

    def test_spec_error(self):
        error_path = EXAMPLES_FOLDER / "spec_error.py"

        with mock.patch.object(env_specs, "log") as log_mock:
            _ = EnvironmentSpec.from_script(error_path)
        
        log_mock.assert_called_once_with(
            MetadataWarning(
                line_number=20,
                message=(
                    "Potential unclosed block 'script' detected. "
                    "A '# ///' block is needed to indicate the end of the block."
                )
            )
        )


class TestSpecText:
    @pytest.mark.parametrize("test_data", envs)
    def test_envspec_pythononly(self, test_data):
        env = EnvironmentSpec(
            "path/to/script.py",
            test_data.raw_spec
        )

        assert env.details.requires_python == test_data.requires_python
        assert env.details.dependencies == test_data.dependencies


    @pytest.mark.parametrize("test_data", envs)
    def test_generate_lockdata(self, test_data, subprocess_run_mock):
        env = EnvironmentSpec(
            "path/to/script.py",
            test_data.raw_spec,
        )
        fake_uv_path = "fake/uv/path"

        lock_data = env.generate_lockdata(fake_uv_path)

        if test_data.dependencies:
            deps = "\n".join(env.details.dependencies)
            # Check the mock output is there
            assert lock_data == MOCK_RUN_STDOUT

            # Check the mock is called correctly
            subprocess_run_mock.assert_called_once_with(
                [
                    fake_uv_path,
                    "pip",
                    "compile",
                    "--universal",
                    "--generate-hashes",
                    "--no-annotate",
                    "--python-version",
                    "3.11",
                    "-",
                ],
                input=deps,
                capture_output=True,
                text=True,
            )

        else:
            # No dependencies, shouldn't call subprocess
            subprocess_run_mock.assert_not_called()

            assert lock_data == "# No Dependencies Declared"


    @pytest.mark.parametrize("test_data", envs)
    def test_requires_python_spec(self, test_data):
        # Test that the requires_python_spec function returns the correct specifierset
        env = EnvironmentSpec(
            "path/to/script.py",
            test_data.raw_spec,
        )

        if test_data.requires_python:
            assert env.details.requires_python_spec == SpecifierSet(
                test_data.requires_python
            )
        else:
            assert env.details.requires_python_spec is None


    @pytest.mark.parametrize("test_data", envs)
    def test_dependencies_spec(self, test_data):
        env = EnvironmentSpec(
            "path/to/script.py",
            test_data.raw_spec,
        )

        assert env.details.dependencies_spec == [
            Requirement(s) for s in test_data.dependencies
        ]


    def test_spec_errors(self, ):
        fake_spec = (
            "requires-python = '!!>=3.10'\n"
            "dependencies = ['invalid_spec!', 'valid_spec>=3.10']\n"
        )

        env = EnvironmentSpec(
            "path/to/script.py",
            fake_spec,
        )

        errs = env.details.errors()

        assert errs == [
            "Invalid python version specifier: '!!>=3.10'",
            "Invalid dependency specification: 'invalid_spec!'",
        ]


    @pytest.mark.parametrize("test_data", envs)
    def test_asdict(self, test_data):
        env = EnvironmentSpec(
            "path/to/script.py",
            test_data.raw_spec,
        )

        assert env.as_dict() == {
            "spec_hash": env.spec_hash,
            "raw_spec": test_data.raw_spec,
            "details": {
                "requires_python": test_data.requires_python,
                "dependencies": test_data.dependencies,
                "tool_table": {},
            },
            "lock_hash": None,
        }
