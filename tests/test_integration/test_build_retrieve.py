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

from ducktools.env import PROJECT_NAME
from ducktools.env.manager import Manager
from ducktools.env.environment_specs import EnvironmentSpec


class TestBuildRetrieve:
    def test_build_retrieve(self, testing_catalogue, test_config):

        manager = Manager(project_name=PROJECT_NAME)

        spec = EnvironmentSpec(
            script_path="path/to/script.py",
            raw_spec="requires-python='>=3.8'\ndependencies=[]\n",
        )

        # Test the env does not exist yet
        assert testing_catalogue.find_env(spec=spec) is None

        python_install = manager._get_python_install(spec=spec)

        real_env = testing_catalogue.create_env(
            spec=spec,
            config=test_config,
            uv_path=manager.retrieve_uv(),
            installer_command=manager.install_base_command(),
            base_python=python_install,
        )

        assert real_env is not None

        retrieve_env = testing_catalogue.find_env(spec=spec)

        assert real_env == retrieve_env
