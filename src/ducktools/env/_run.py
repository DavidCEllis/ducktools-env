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
Short implementation of the `dtrun` command.

Unlike ducktools-env run, `dtrun` doesn't take any arguments other than the script name
and arguments to pass on to the following script.

This means it doesn't need to construct the argument parser as everything is passed
on to the script being run.
"""
import sys
import os.path

from . import PROJECT_NAME
from .manager import Manager


def run():
    # First argument is the path to this script
    _, app, *args = sys.argv

    # This has been invoked by dtrun, but errors should show ducktools-env
    command = "ducktools-env"

    manager = Manager(
        project_name=PROJECT_NAME,
        command=command,
    )

    try:
        if os.path.isfile(app):
            manager.run_script(
                script_path=app,
                script_args=args,
            )
        else:
            manager.run_registered_script(
                script_name=app,
                script_args=args,
            )
    except RuntimeError as e:
        msg = "\n".join(e.args) + "\n"
        if sys.stderr:
            sys.stderr.write(msg)
        sys.exit(1)

    sys.exit(0)
