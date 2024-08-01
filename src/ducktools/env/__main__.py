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

import argparse
from ducktools.lazyimporter import LazyImporter, ModuleImport, FromImport

_laz = LazyImporter(
    [
        FromImport(".run", "run_script"),
        FromImport(".scripts.clear_cache", "clear_cache")
    ],
    globs=globals()
)


def main():
    parser = argparse.ArgumentParser(
        prog="ducktools-env",
        description="Script runner and bundler for scripts with inline dependencies",
        prefix_chars="+/",
    )

    parser.add_argument(
        "command",
        choices=["run", "bundle", "clear_cache"],
        help="ducktools-env commands"
    )

    matched, pass_on = parser.parse_known_args()

    if matched.command == "run":
        _laz.run_script(pass_on)
    elif matched.command == "bundle":
        raise NotImplementedError("Bundle script not yet implemented.")
    elif matched.command == "clear_cache":
        if pass_on:
            print("clear_cache command does not take any additional arguments")
        _laz.clear_cache()
    else:
        # Should be unreachable
        raise ValueError("Invalid command")


if __name__ == "__main__":
    main()
