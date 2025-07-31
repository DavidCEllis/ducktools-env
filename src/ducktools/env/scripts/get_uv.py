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
import sys


from .._logger import log
from .. import _lazy_imports as _laz


uv_versionspec = ">=0.7.0"
uv_versionre = r"^uv (?P<uv_ver>\d+\.\d+\.\d+)"

uv_download = "bin/uv.exe" if sys.platform == "win32" else "bin/uv"


def get_local_uv():
    """
    Retrieve the path to a 'uv' executable if it is installed

    :return: path to uv
    """
    uv_path = _laz.shutil.which("uv")
    if uv_path:
        try:
            version_output = _laz.subprocess.run([uv_path, "-V"], capture_output=True, text=True)
        except (FileNotFoundError, _laz.subprocess.CalledProcessError):
            return None

        ver_match = _laz.re.match(uv_versionre, version_output.stdout.strip())
        if ver_match:
            uv_version = ver_match.group("uv_ver")
            if uv_version not in _laz.SpecifierSet(uv_versionspec):
                log(
                    f"Local uv install version {uv_version!r} "
                    f"does not satisfy the ducktools.env specifier {uv_versionspec!r}"
                )
                return None

    return uv_path


def get_available_pythons(uv_path: str) -> list[str]:
    """
    Get all python install version numbers available from UV

    :param uv_path: Path to the UV executable
    :return: list of version strings
    """
    # CPython installs listed by UV - only want downloadable installs
    version_re = _laz.re.compile(
        r"(?m)^cpython-(?P<version>\d+.\d+.\d+(?:a|b|rc)?\d*).*<download available>$"
    )
    data = _laz.subprocess.run(
        [
            uv_path,
            "python",
            "list",
            "--all-versions",
        ],
        capture_output=True,
        text=True,
        check=True,
    )

    matches = version_re.findall(data.stdout)

    return matches


def install_uv_python(*, uv_path: str, version_str: str) -> None:
    _laz.subprocess.run(
        [
            uv_path,
            "python",
            "install",
            version_str,
        ],
        check=True,
    )
