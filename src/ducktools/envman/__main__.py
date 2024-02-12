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
A simple 'main' script showing usage - use all default settings.
"""
import sys
import subprocess

from . import Config, Catalogue, EnvironmentSpec


def main():
    args_to_python = sys.argv[1:]
    for item in args_to_python:
        if item.endswith(".py"):
            script_file = item
            break
    else:
        raise ValueError("Must provide a path to a python script within the arguments.")

    spec = EnvironmentSpec.from_file(script_file)

    config = Config()
    catalogue = Catalogue.from_config(config)

    env = catalogue.find_or_create_env(spec)

    sys.stderr.write(f"Using environment at: {env.cache_path}\n")

    subprocess.run([env.python_path, *args_to_python])


main()
