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


# Table Structure

## Specs ##
# id - int
# env_id - int - Environment that matches in environments table
# spec_text - string - The source text of the specification

## Packages ##

# id - int
# env_id - int - Environment where these packages are installed
# package_name - str
# version_no - string version

## Environments ##

# id - int (env_id in other tables)
# environment_folder - str - path to environment
# environment_exe - str - path to environment exe
# environment_created - datetime - when the env was created
# environment_used - datetime - last time the environment was used

import os.path
import sqlite3

from .config import Config


def make_db(config: Config, exist_ok=True):
    """
    Create the database file

    :param config: envman configuration file
    :param exist_ok: return if the database exists, do not error
    :return:
    """
    db_path = config.db_path
    if os.path.exists(db_path):
        if exist_ok:
            return
        else:
            raise FileExistsError(f"Database file {db_path} already exists")

