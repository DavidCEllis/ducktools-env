import pytest

import sys
import os.path

from ducktools.envman.python_finders.shared import PythonVersion
from ducktools.envman.python_finders.winpy_finder import get_py_install_versions

known_versions = [
    PythonVersion.from_str(
        "3.10",
        os.path.join(os.path.expandvars("%LOCALAPPDATA%"), "Programs", "Python", "Python310", "python.exe"),
    ),
    PythonVersion.from_str(
        "3.11",
        os.path.join(os.path.expandvars("%LOCALAPPDATA%"), "Programs", "Python", "Python311", "python.exe"),
    ),
    PythonVersion.from_str(
        "3.12",
        os.path.join(os.path.expandvars("%LOCALAPPDATA%"), "Programs", "Python", "Python312", "python.exe"),
    ),
]


installed_python = [item for item in known_versions if os.path.exists(item.executable)]


@pytest.mark.skipif(sys.platform != "win32", reason="Windows only test")
def test_winpy_real():
    versions = get_py_install_versions(precise=False)

    for ver in installed_python:
        assert ver in versions
