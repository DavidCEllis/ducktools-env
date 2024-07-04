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

from ducktools.classbuilder.prefab import Prefab, attribute
from ducktools.lazyimporter import (
    LazyImporter,
    TryExceptImport,
    ModuleImport,
    MultiFromImport,
)
from ducktools.scriptmetadata import parse_file


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


class EnvironmentSpec(Prefab):
    """
    Environment specification details in toml format

    Matching Python "inline script metadata"
    """
    raw_spec: str | None
    tool_table: str = "envman"

    # Internal attributes used for caches
    _initialized: bool = attribute(default=False, init=False, exclude_field=True)
    _requires_python: str | None = attribute(default=False, init=False, exclude_field=True)
    _dependencies: list[str] = attribute(default_factory=list, init=False, exclude_field=True)
    _extras: dict = attribute(default_factory=dict, init=False, exclude_field=True)

    def _parse_raw(self):
        if self.raw_spec:
            # Parse the raw data as toml to extract requirements
            requirement_data = _laz.tomllib.loads(self.raw_spec)

            tool_block = (
                requirement_data.get("tool", {})
                .get("ducktools", {})
                .get(self.tool_table, {})
            )
            requires_python = requirement_data.get("requires-python", None)
            dependencies = requirement_data.get("dependencies", [])

            self._requires_python = requires_python
            self._dependencies = dependencies
            self._extras = tool_block

        self._initialized = True

    @classmethod
    def from_file(cls, script_path, tool_table="envman"):
        parsed_data = parse_file(script_path)

        # Display any warning messages
        for warning in parsed_data.warnings:
            _laz.warnings.warn(warning)

        # noinspection PyArgumentList
        return cls(
            raw_spec=parsed_data.blocks.get("script"),
            tool_table=tool_table,
        )

    @property
    def requires_python(self) -> str | None:
        if not self._initialized:
            self._parse_raw()
        return self._requires_python

    @property
    def dependencies(self) -> list[str]:
        if not self._initialized:
            self._parse_raw()
        return self._dependencies

    @property
    def extras(self) -> dict:
        if not self._initialized:
            self._parse_raw()
        return self._extras

    @property
    def requires_python_spec(self):
        return _laz.SpecifierSet(self.requires_python) if self.requires_python else None

    @property
    def dependencies_spec(self):
        return [_laz.Requirement(dep) for dep in self.dependencies]

    def errors(self) -> list[str]:
        error_details = []

        if self.requires_python:
            try:
                _laz.SpecifierSet(self.requires_python)
            except _laz.InvalidSpecifier:
                error_details.append(
                    f"Invalid python version specifier: {self.requires_python!r}"
                )
        for dep in self.dependencies:
            try:
                _laz.Requirement(dep)
            except _laz.InvalidRequirement:
                error_details.append(f"Invalid dependency specification: {dep!r}")

        return error_details
