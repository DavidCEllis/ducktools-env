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


class EnvironmentDetails(Prefab, kw_only=True):
    requires_python: str | None
    dependencies: list[str]
    tool_table: dict

    @property
    def requires_python_spec(self):
        return _laz.SpecifierSet(self.requires_python) if self.requires_python else None

    @property
    def dependencies_spec(self):
        return [_laz.Requirement(dep) for dep in self.dependencies]

    @property
    def bundle_table(self) -> dict:
        return self.tool_table.get("bundle", {})

    @property
    def data_sources(self) -> list[str] | None:
        return self.bundle_table.get("data")

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
    script_path: str
    raw_spec: str
    lockdata: str | None

    def __init__(
        self,
        script_path: str,
        raw_spec: str,
        *,
        lockdata: str | None = None,
        spec_hash: str | None = None,
        details: EnvironmentDetails | None = None,
    ) -> None:
        self.script_path = script_path
        self.raw_spec = raw_spec
        self.lockdata = lockdata

        self._spec_hash: str | None = spec_hash
        self._lock_hash: str | None = None
        self._details: EnvironmentDetails | None = details

    @classmethod
    def from_script(cls, script_path, lockdata: str | None = None):
        raw_spec = scriptmetadata.parse_file(script_path).blocks.get("script", "")
        return cls(
            script_path=script_path,
            raw_spec=raw_spec,
            lockdata=lockdata
        )

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
    
    @property
    def lock_hash(self) -> str:
        if self.lockdata and self._lock_hash is None:
            lock_bytes = self.lockdata.encode("utf8")
            self._lock_hash = _laz.hashlib.sha3_256(lock_bytes).hexdigest()
        return self._lock_hash

    def parse_raw(self) -> EnvironmentDetails:
        base_table = _laz.tomllib.loads(self.raw_spec)

        requires_python = base_table.get("requires-python", None)
        dependencies = base_table.get("dependencies", [])

        tool_table = (
            base_table.get("tool", {})
            .get("ducktools", {})
            .get("env", {})
        )

        # noinspection PyArgumentList
        return EnvironmentDetails(
            requires_python=requires_python,
            dependencies=dependencies,
            tool_table=tool_table,
        )

    def generate_lockdata(self, uv_path: str) -> str | None:
        """
        Generate a lockfile from the dependency data
        :param uv_path: Path to the UV executable
        :return: lockfile data as a text string or None if there are no dependencies
        """
        if not self.lockdata:
            # Only go through the process if there is anything to lock
            if deps := "\n".join(self.details.dependencies):
                python_version = []
                if python_spec := self.details.requires_python_spec:
                    # Try to find the minimum python version that satisfies the spec
                    for s in python_spec:
                        if s.operator in {"==", ">=", "~="}:
                            python_version = ["--python-version", s.version]
                            break

                lock_cmd = [
                    uv_path,
                    "pip",
                    "compile",
                    "--universal",
                    "--generate-hashes",
                    "--no-annotate",
                    *python_version,
                    "-",
                ]

                print("Locking dependency tree")
                lock_output = _laz.subprocess.run(
                    lock_cmd,
                    input=deps,
                    capture_output=True,
                    text=True,
                )

                self.lockdata = lock_output.stdout

            else:
                # There are no dependencies - Make a note of this
                # This makes lockdata Truthy
                self.lockdata = "# No Dependencies Declared"

        return self.lockdata

    def as_dict(self):
        return {
            "spec_hash": self.spec_hash,
            "raw_spec": self.raw_spec,
            "lock_hash": self.lock_hash,
            "details": as_dict(self.details),
        }
