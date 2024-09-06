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

from ducktools.env.environment_specs import EnvironmentSpec
from ducktools.env.environment_specs import _laz  # noqa

from ducktools.classbuilder.prefab import prefab, attribute
import pytest

from packaging.specifiers import SpecifierSet
from packaging.requirements import Requirement


MOCK_RUN_STDOUT = "<MOCK DATA>"


@pytest.fixture
def subprocess_run_mock():
    with mock.patch.object(_laz, "subprocess") as sp:
        run_mock = mock.MagicMock()
        run_return_mock = mock.MagicMock()
        run_return_mock.stdout = MOCK_RUN_STDOUT
        run_mock.return_value = run_return_mock

        sp.run = run_mock
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


@pytest.mark.parametrize("test_data", envs)
def test_envspec_pythononly(test_data):
    env = EnvironmentSpec(
        "path/to/script.py",
        test_data.raw_spec
    )

    assert env.details.requires_python == test_data.requires_python
    assert env.details.dependencies == test_data.dependencies


@pytest.mark.parametrize("test_data", envs)
def test_generate_lockdata(test_data, subprocess_run_mock):
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
def test_requires_python_spec(test_data):
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
def test_dependencies_spec(test_data):
    env = EnvironmentSpec(
        "path/to/script.py",
        test_data.raw_spec,
    )

    assert env.details.dependencies_spec == [
        Requirement(s) for s in test_data.dependencies
    ]


def test_spec_errors():
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
def test_asdict(test_data):
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
