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

from ducktools.envman.environment_spec import EnvironmentSpec

from prefab_classes import prefab, attribute
import pytest


@prefab
class DataSet:
    raw_spec: str
    requires_python: str | None = None
    dependencies: list[str] = attribute(default_factory=list)
    extras: dict = attribute(default_factory=dict)


envs = [
    DataSet(
        raw_spec=(
            "requires-python = '>=3.10'\n"
            "dependencies = []\n"
        ),
        requires_python=">=3.10",
    ),
    DataSet(
        raw_spec=(
            "requires-python = '>=3.11'\n"
            "dependencies = ['prefab-classes>=0.10.0']\n"
        ),
        requires_python=">=3.11",
        dependencies=["prefab-classes>=0.10.0"],
    )
]


@pytest.mark.parametrize("test_data", envs)
def test_envspec_pythononly(test_data):
    env = EnvironmentSpec(test_data.raw_spec)

    assert env.requires_python == test_data.requires_python
    assert env.dependencies == test_data.dependencies
    assert env.extras == test_data.extras
