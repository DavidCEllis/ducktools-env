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


from ducktools.envman.inline_dependencies import EnvironmentSpec


class TestBuildRetrieve:
    def test_build_retrieve(self, testing_catalogue):
        spec = EnvironmentSpec(
            "requires-python='>=3.10'\n"
            "dependencies=[]\n",
        )

        # Test the env does not exist yet
        assert testing_catalogue.find_env(spec) is None

        real_env = testing_catalogue.find_or_create_env(spec)

        assert real_env is not None

        retrieve_env = testing_catalogue.find_env(spec)

        assert real_env == retrieve_env
