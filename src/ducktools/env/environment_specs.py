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

import enum

from ducktools.lazyimporter import (
    LazyImporter,
    FromImport,
    ModuleImport,
    MultiFromImport,
    TryExceptImport,
)

from ducktools.classbuilder.prefab import Prefab, as_dict
import ducktools.scriptmetadata as scriptmetadata


# Lazy importers for modules that may not be used
_laz = LazyImporter(
    [
        TryExceptImport(
            "tomllib",
            "tomli",
            "tomllib",
        ),
        ModuleImport("warnings"),
        ModuleImport("subprocess"),
        ModuleImport("hashlib"),
        MultiFromImport(
            "packaging.requirements",
            ["Requirement", "InvalidRequirement"],
        ),
        MultiFromImport(
            "packaging.specifiers",
            ["SpecifierSet", "InvalidSpecifier"],
        ),
        FromImport(
            "importlib", "metadata"
        ),
    ],
)


class SpecType(enum.IntEnum):
    """
    Enum to inform EnvironmentSpec how to parse the metadata
    if needed.
    """
    INLINE_METADATA = 1
    WHEEL_METADATA = 2


class EnvironmentDetails(Prefab, kw_only=True):
    requires_python: str | None
    dependencies: list[str]

    project_name: str | None
    project_owner: str | None
    project_version: str | None

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


class EnvironmentSpec:
    spec_type: SpecType
    raw_spec: str

    def __init__(
            self,
            spec_type: SpecType,
            raw_spec: str,
            *,
            spec_hash: str | None = None,
            details: EnvironmentDetails | None = None,
    ) -> None:
        self.spec_type = spec_type
        self.raw_spec = raw_spec

        self._spec_hash: str | None = spec_hash
        self._details: EnvironmentDetails | None = details

    @classmethod
    def from_script(cls, script_path):
        spec_type = SpecType.INLINE_METADATA
        raw_spec = scriptmetadata.parse_file(script_path).blocks.get("script", "")
        return cls(spec_type=spec_type, raw_spec=raw_spec)

    @property
    def details(self) -> EnvironmentDetails:
        if self._details is None:
            self._details = self.parse_raw()
        return self._details

    @property
    def spec_hash(self) -> str:
        if self._spec_hash is None:
            spec_bytes = self.raw_spec.encode("utf8")
            self._spec_hash = _laz.hashlib.sha3_256(spec_bytes).hexdigest()
        return self._spec_hash

    def parse_raw(self) -> EnvironmentDetails:
        base_table = _laz.tomllib.loads(self.raw_spec)

        data_table = (
            base_table.get("tool", {})
            .get("ducktools", {})
            .get("env", {})
        )

        env_project_table = data_table.get("project", {})

        if self.spec_type == SpecType.INLINE_METADATA:
            requires_python = base_table.get("requires-python", None)
            dependencies = base_table.get("dependencies", [])

            project_name = env_project_table.get("name", None)
            version = env_project_table.get("version", None)
            owner = env_project_table.get("owner", None)

        # I think spec_type is going to be removed and everything
        # will be handled by script metadata.
        elif self.spec_type == SpecType.WHEEL_METADATA:  # pragma: no cover
            raise EnvironmentError("Wheel based spec not implemented")

        else: # pragma: no cover
            raise TypeError(f"'spec_type' must be an instance of {SpecType.__name__!r}")

        # noinspection PyArgumentList
        return EnvironmentDetails(
            requires_python=requires_python,
            dependencies=dependencies,
            project_name=project_name,
            project_owner=owner,
            project_version=version,
        )

    def generate_lockfile(self, uv_path: str) -> str | None:
        """
        Generate a lockfile from the dependency data
        :param uv_path: Path to the UV executable
        :return: lockfile data as a text string or None if there are no dependencies
        """
        # Only make a lockfile if there is anything to lock
        if deps := "\n".join(self.details.dependencies):
            lock_cmd = [
                uv_path,
                "pip",
                "compile",
                "--universal",
                "--no-strip-markers",
                "--generate-hashes",
                "-",
            ]

            print("Locking dependency tree")
            lock_output = _laz.subprocess.run(
                lock_cmd,
                input=deps,
                capture_output=True,
                text=True,
            )

            hash_line = f"# Original Specification Hash: {self.spec_hash}\n"

            return hash_line + lock_output.stdout

        return None

    def as_dict(self):
        return {
            "spec_hash": self.spec_hash,
            "spec_type": self.spec_type,
            "raw_spec": self.raw_spec,
            "details": as_dict(self.details),
        }
