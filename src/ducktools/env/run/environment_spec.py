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

from __future__ import annotations

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


class InlineSpec(Prefab):
    """
    Environment specification details in toml format

    Matching Python "inline script metadata"
    """
    raw_spec: str | None
    tool_table: str = "env"

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
