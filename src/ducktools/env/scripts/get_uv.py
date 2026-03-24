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
from .._logger import log
from .. import _lazy_imports as _laz


uv_versionspec = ">=0.10.0"
uv_versionre = r"^uv (?P<uv_ver>\d+\.\d+\.\d+)"


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
