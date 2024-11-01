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


from ducktools.lazyimporter import (
    LazyImporter,
    FromImport,
    ModuleImport,
    MultiFromImport,
    TryExceptImport,
)

laz = LazyImporter(
    [
        # Stdlib and dependency imports
        ModuleImport("hashlib"),
        ModuleImport("json"),
        ModuleImport("re"),
        ModuleImport("shutil"),
        ModuleImport("sqlite3", asname="sql"),
        ModuleImport("subprocess"),
        ModuleImport("tempfile"),
        ModuleImport("warnings"),
        ModuleImport("zipfile"),

        MultiFromImport(
            "ducktools.pythonfinder",
            ["list_python_installs", "PythonInstall"],
        ),
        FromImport(
            "ducktools.pythonfinder.shared",
            "get_uv_pythons",
            "get_installed_uv_pythons"
        ),
        FromImport(
            "importlib",
            "metadata"
        ),
        FromImport(
            "tempfile",
            "TemporaryDirectory"
        ),
        FromImport(
            "urllib.request",
            "urlopen"
        ),

        MultiFromImport(
            "packaging.requirements",
            ["Requirement", "InvalidRequirement"],
        ),
        MultiFromImport(
            "packaging.specifiers",
            ["SpecifierSet", "InvalidSpecifier"],
        ),
        MultiFromImport(
            "packaging.version",
            ["Version", "InvalidVersion"]
        ),

        TryExceptImport(
            "tomllib",
            "tomli",
            "tomllib",
        ),
    ],
)
