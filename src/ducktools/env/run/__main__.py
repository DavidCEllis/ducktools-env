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

    sys.stderr.write(f"Using environment at: {env.path}\n")

    subprocess.run([env.python_path, *args_to_python])


if __name__ == "__main__":
    main()