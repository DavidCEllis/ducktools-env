# DuckTools-EnvMan
# Copyright (C) 2024 David C Ellis
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Lesser General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Lesser General Public License for more details.
#
# You should have received a copy of the GNU Lesser General Public License
# along with this program.  If not, see <https://www.gnu.org/licenses/>.


"""
Search the Windows registry to find python installs

Based on PEP 514 registry entries.
"""

import winreg  # noqa  # pycharm seems to think winreg doesn't exist in python3.12

from ..shared import PythonInstall

exclude_companies = {
    "PyLauncher",  # pylauncher is special cased to be ignored
}


check_pairs = [
    # Keys defined in PEP 514
    (winreg.HKEY_CURRENT_USER, "SOFTWARE\\Python"),
    (winreg.HKEY_LOCAL_MACHINE, "SOFTWARE\\Python"),
    # For system wide 32 bit python installs
    (winreg.HKEY_LOCAL_MACHINE, "SOFTWARE\\Wow6432Node\\Python"),
]


def get_registered_pythons() -> list[PythonInstall]:
    python_installs: list[PythonInstall] = []

    for base, py_folder in check_pairs:
        try:
            base_key = winreg.OpenKey(base, py_folder)
        except FileNotFoundError:
            continue

        subkeys, _, _ = winreg.QueryInfoKey(base_key)

        # Query the base folder eg: HKEY_LOCAL_MACHINE\SOFTWARE\Python
        # The values here should be "companies" as defined in the PEP
        for i in range(subkeys):
            company = winreg.EnumKey(base_key, i)
            if company not in exclude_companies:
                company_key = winreg.OpenKey(base_key, company)
                comp_subkeys, comp_values, _ = winreg.QueryInfoKey(company_key)
                comp_metadata = {}
                for j in range(comp_values):
                    name, data, _ = winreg.EnumValue(company_key, j)
                    comp_metadata[f"Company{name}"] = data

                for j in range(comp_subkeys):
                    metadata = {**comp_metadata}
                    py_keyname = winreg.EnumKey(company_key, j)
                    py_key = winreg.OpenKey(company_key, py_keyname)
                    _, py_values, _ = winreg.QueryInfoKey(py_key)
                    for k in range(py_values):
                        name, data, _ = winreg.EnumValue(py_key, k)
                        metadata[name] = data

                    install_key = winreg.OpenKey(py_key, "InstallPath")
                    python_path = winreg.QueryValueEx(install_key, "ExecutablePath")[0]
                    python_version = metadata["Version"]
                    architecture = metadata["SysArchitecture"]

                    python_installs.append(
                        PythonInstall.from_str(
                            version=python_version,
                            executable=python_path,
                            architecture=architecture,
                            metadata=metadata,
                        )
                    )

    return python_installs
