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

import os.path
import sys

from ducktools.lazyimporter import LazyImporter, ModuleImport
from ducktools.env.platform_paths import ManagedPaths
from ducktools.env.scripts.get_pip import retrieve_pip

_laz = LazyImporter(
    [
        ModuleImport("shutil"),
        ModuleImport("subprocess"),
    ]
)


uv_versionspec = "~=0.4.0"

uv_download = "bin/uv.exe" if sys.platform == "win32" else "bin/uv"


def retrieve_uv(paths: ManagedPaths) -> str | None:
    if os.path.exists(paths.uv_executable):
        uv_path = paths.uv_executable
    else:
        pip_install = retrieve_pip(paths=paths)
        with paths.build_folder() as build_folder:

            install_folder = os.path.join(build_folder, "uv")

            uv_dl = os.path.join(install_folder, uv_download)

            pip_command = [
                sys.executable,
                pip_install,
                "--disable-pip-version-check",
                "install",
                "-q",
                f"uv{uv_versionspec}",
                "--only-binary=:all:",
                "--target",
                install_folder,
            ]

            # Download UV with pip - handles getting the correct platform version
            try:
                _laz.subprocess.run(
                    pip_command,
                    check=True,
                )
            except _laz.subprocess.CalledProcessError:
                uv_path = None
            else:
                # Copy the executable out of the pip install
                _laz.shutil.copy(uv_dl, paths.uv_executable)
                uv_path = paths.uv_executable

                version_command = [uv_path, "-V"]
                version_output = _laz.subprocess.run(version_command, capture_output=True, text=True)
                uv_version = version_output.stdout.split()[1]
                with open(f"{uv_path}.version", 'w') as ver_file:
                    ver_file.write(uv_version)

    return uv_path
