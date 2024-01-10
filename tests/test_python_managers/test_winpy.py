import pytest

import sys
import os.path

from ducktools.envman.python_finders.shared import PythonInstall
from ducktools.envman.python_finders.winpy_finder import get_py_install_versions


def _python_folder(verno: str) -> str:
    return os.path.join(
        os.path.expandvars("%LOCALAPPDATA%"),
        "Programs",
        "Python",
        f"Python3{verno}",
        "python.exe",
    )


known_versions = [
    PythonInstall.from_str(
        "3.10",
        _python_folder("310"),
    ),
    PythonInstall.from_str(
        "3.11",
        _python_folder("311"),
    ),
    PythonInstall.from_str(
        "3.12",
        _python_folder("312"),
    ),
]


installed_python = [item for item in known_versions if os.path.exists(item.executable)]


@pytest.mark.skipif(sys.platform != "win32", reason="Windows only test")
def test_winpy_real():
    versions = get_py_install_versions(precise=False)

    for ver in installed_python:
        assert ver in versions
