import os
import os.path

from ..shared import PythonInstall


PYENV_VERSIONS_FOLDER = os.path.expanduser(
    os.path.join("~", ".pyenv", "pyenv-win", "versions")
)


def get_pyenv_pythons(
        versions_folder: str | os.PathLike = PYENV_VERSIONS_FOLDER,
) -> list[PythonInstall]:

    if not os.path.exists(versions_folder):
        return []

    python_versions = []
    for p in os.scandir(versions_folder):
        executable = os.path.join(p.path, "python.exe")

        if os.path.exists(executable):
            match p.name.split("-"):
                case (version, arch):
                    # win32 in pyenv name means 32 bit python install
                    # 'arm' is the only alternative which will be 64bit
                    arch = "32bit" if arch == "win32" else "64bit"
                    python_versions.append(
                        PythonInstall.from_str(version, executable, architecture=arch)
                    )
                case (version, ):
                    # If no arch given pyenv will be 64 bit
                    python_versions.append(
                        PythonInstall.from_str(version, executable, architecture="64bit")
                    )
                case _:
                    pass  # Skip unrecognised versions

    python_versions.sort(key=lambda x: x.version, reverse=True)

    return python_versions
