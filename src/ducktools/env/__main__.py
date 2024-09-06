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
import sys

import argparse
from ducktools.lazyimporter import LazyImporter, FromImport

from ducktools.env import __version__, PROJECT_NAME

_laz = LazyImporter(
    [
        FromImport("ducktools.env.manager", "Manager"),
    ]
)


def main():
    parser = argparse.ArgumentParser(
        prog="ducktools-env",
        description="Script runner and bundler for scripts with inline dependencies",
    )

    parser.add_argument("-V", "--version", action="version", version=__version__)

    subparsers = parser.add_subparsers(dest="command", required=True)

    # 'run' command and args
    run_parser = subparsers.add_parser(
        "run",
        help="Launch the provided python script with inline dependencies",
    )

    run_parser.add_argument("script_filename", help="Path to the script to run")

    run_lock_group = run_parser.add_mutually_exclusive_group()
    run_lock_group.add_argument(
        "--with-lock",
        help="Include a lockfile to use when running the script",
        action="store"
    )
    run_lock_group.add_argument(
        "--generate-lock",
        help="Generate a lockfile based on the dependencies in the script",
        action="store_true",
    )

    # 'bundle' command and args
    bundle_parser = subparsers.add_parser(
        "bundle",
        help="Bundle the provided python script with inline dependencies into a python zipapp",
    )

    bundle_parser.add_argument("script_filename", help="Path to the script to bundle into a zipapp")
    bundle_parser.add_argument(
        "-o", "--output",
        help="Output to given filename",
        action="store",
    )

    bundle_lock_group = bundle_parser.add_mutually_exclusive_group()
    bundle_lock_group.add_argument(
        "--with-lock",
        help="Include a lockfile to use when running the script",
        action="store"
    )
    bundle_lock_group.add_argument(
        "--generate-lock",
        help="Generate a lockfile to use when unbundling",
        action="store_true"
    )

    # 'generate_lock' command and args
    generate_lock_parser = subparsers.add_parser(
        "generate_lock",
        help="Generate a lockfile based on inline dependencies in a script"
    )

    generate_lock_parser.add_argument(
        "script_filename",
        help="Path to the script to use to generate a lockfile"
    )

    generate_lock_parser.add_argument(
        "-o", "--output",
        help="Output to given filename",
    )

    # 'clear_cache' command and args
    clear_cache_parser = subparsers.add_parser(
        "clear_cache",
        help="clear the temporary environment cache folder",
    )

    clear_cache_parser.add_argument(
        "--full",
        action="store_true",
        help="clear the full ducktools/env application folder",
    )

    # 'rebuild_env' command and args
    create_zipapp_parser = subparsers.add_parser(
        "rebuild_env",
        help="Recreate the ducktools-env library cache from the installed package"
    )

    create_zipapp_parser.add_argument(
        "--zipapp",
        action="store_true",
        help="Also create the portable ducktools.pyz zipapp",
    )

    args, extras = parser.parse_known_args()

    # Finally create a manager
    manager = _laz.Manager(PROJECT_NAME)

    if args.command == "run":
        if args.generate_lock:
            lockdata = manager.get_lockdata(
                script_file=args.script_filename,
            )
            lock_path = f"{args.script_filename}.lock"
            with open(lock_path, 'w') as f:
                f.write(lockdata)
        elif lock_path := args.with_lock:
            with open(lock_path, 'r') as f:
                lockdata = f.read()
        else:
            lockdata = None

        manager.run_direct_script(
            script_file=args.script_filename,
            args=extras,
            lockdata=lockdata,
        )
    elif args.command == "bundle":
        if extras:
            arg_text = ' '.join(extras)
            sys.stderr.write(f"Unrecognised arguments: {arg_text}")
            return
        
        if args.generate_lock:
            lockdata = manager.get_lockdata(
                script_file=args.script_filename,
            )
        elif lock_path := args.with_lock:
            with open(lock_path, 'r') as f:
                lockdata = f.read()
        else:
            lockdata = None

        manager.create_bundle(
            script_file=args.script_filename,
            output_file=args.output,
            lockdata=lockdata,
        )
    elif args.command == "generate_lock":
        lock_data = manager.get_lockdata(
            script_file=args.script_filename,
        )
        out_path = args.output if args.output else f"{args.script_filename}.lock"
        with open(out_path, "w") as f:
            f.write(lock_data)

    elif args.command == "clear_cache":
        if extras:
            arg_text = ' '.join(extras)
            sys.stderr.write(f"Unrecognised arguments: {arg_text}")
            return

        if args.full:
            manager.clear_project_folder()
        else:
            manager.clear_temporary_cache()
    elif args.command == "rebuild_env":
        if extras:
            arg_text = ' '.join(extras)
            sys.stderr.write(f"Unrecognised arguments: {arg_text}")
            return

        manager.build_env_folder()
        if args.zipapp:
            manager.build_zipapp()
    else:
        # Should be unreachable
        raise ValueError("Invalid command")


if __name__ == "__main__":
    main()
