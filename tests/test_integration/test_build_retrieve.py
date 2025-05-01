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
