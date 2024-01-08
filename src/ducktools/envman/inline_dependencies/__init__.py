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

"""
Handle parsing of inline script dependency data.
"""

import os

from prefab_classes import prefab, attribute
from ducktools.lazyimporter import LazyImporter, TryExceptImport, ModuleImport, MultiFromImport
from ducktools.script_metadata_parser import parse_file


# Lazy importers for modules that may not be used
_laz = LazyImporter(
    [
        TryExceptImport(
            "tomllib",
            "tomli",
            "tomllib",
        ),
        ModuleImport("warnings"),
        MultiFromImport(
            "packaging.requirements",
            ["Requirement", "InvalidRequirement"],
        ),
        MultiFromImport(
            "packaging.specifiers",
            ["SpecifierSet", "InvalidSpecifier"],
        ),
    ],
)


class SpecificationError(Exception):
    pass


@prefab
class EnvironmentSpec:
    requires_python: str | None = attribute(default=None)
    dependencies: list[str] = attribute(default_factory=list())

    def errors(self) -> list[str]:
        error_details = []

        if self.requires_python:
            try:
                _laz.SpecifierSet(self.requires_python)
            except _laz.InvalidSpecifier:
                error_details.append(f"Invalid python version specifier: {self.requires_python!r}")
        for dep in self.dependencies:
            try:
                _laz.Requirement(dep)
            except _laz.InvalidRequirement:
                error_details.append(f"Invalid dependency specification: {dep!r}")

        return error_details


def get_requirements(
        script_path: os.PathLike | str,
        check_errors: bool = True,
) -> EnvironmentSpec:
    """
    Get the python version and dependencies

    :param script_path: Path to the python script to parse for environment requirements
    :param check_errors: Check the resulting specification has valid version
                         and dependency specifiers.
    :return: Dictionary with "requires-python" and "dependencies"
    """
    parsed_data = parse_file(script_path)

    # Display any warning messages
    for warning in parsed_data.warnings:
        _laz.warnings.warn(warning)

    # Parse the TOML
    if raw_metadata := parsed_data.blocks.get("script"):
        requirement_data = _laz.tomllib.loads(raw_metadata)

        requirements = EnvironmentSpec(
            requirement_data.get("requires-python", None),
            requirement_data.get("dependencies", []),
        )
    else:
        requirements = EnvironmentSpec()

    if check_errors:
        if errors := requirements.errors():
            raise SpecificationError(", ".join(errors))

    return requirements
