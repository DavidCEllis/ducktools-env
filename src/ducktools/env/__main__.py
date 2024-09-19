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
import os

import argparse

from collections.abc import Callable, Generator, Iterable

from ducktools.lazyimporter import LazyImporter, FromImport

from ducktools.env import __version__, PROJECT_NAME

_laz = LazyImporter(
    [
        FromImport("ducktools.env.manager", "Manager"),
        FromImport("ducktools.env.environment_specs", "EnvironmentSpec"),
    ]
)


class FixedArgumentParser(argparse.ArgumentParser):
    """
    The builtin argument parser uses shutil to figure out the terminal width
    to display help info. This one replaces the function that calls help info
    and plugs in a value for width.

    This prevents the unnecessary import.
    """
    def _get_formatter(self):
        # Calculate width
        try:
            columns = int(os.environ['COLUMNS'])
        except (KeyError, ValueError):
            try:
                size = os.get_terminal_size()
            except (AttributeError, ValueError, OSError):
                # get_terminal_size unsupported
                columns = 80
            else:
                columns = size.columns

        # noinspection PyArgumentList
        return self.formatter_class(prog=self.prog, width=columns-2)


def get_parser(exit_on_error=True) -> FixedArgumentParser:
    parser = FixedArgumentParser(
        prog="ducktools-env",
        description="Script runner and bundler for scripts with inline dependencies",
        exit_on_error=exit_on_error,
    )

    parser.add_argument("-V", "--version", action="version", version=__version__)

    subparsers = parser.add_subparsers(dest="command", required=True)

    # 'run' command and args
    run_parser = subparsers.add_parser(
        "run",
        help="Launch the provided python script with inline dependencies",
    )

    run_parser.add_argument("script_filename", help="Path to the script to run")
    run_parser.add_argument(
        "script_args",
        nargs="*",
        help="Arguments to pass on to the script",
    )

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

    bundle_parser.add_argument(
        "script_filename",
        help="Path to the script to bundle into a zipapp",
    )
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
        help="Generate a lockfile based on inline dependencies in a script",
    )

    generate_lock_parser.add_argument(
        "script_filename",
        help="Path to the script to use to generate a lockfile",
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
        help="Recreate the ducktools-env library cache from the installed package",
    )

    create_zipapp_parser.add_argument(
        "--zipapp",
        action="store_true",
        help="Also create the portable ducktools.pyz zipapp",
    )

    list_parser = subparsers.add_parser(
        "list",
        help="List the Python virtual environments managed by ducktools-env",
    )

    list_type_group = list_parser.add_mutually_exclusive_group()
    list_type_group.add_argument(
        "--temp",
        action="store_true",
        help="Only list temporary environments",
    )
    list_type_group.add_argument(
        "--app",
        action="store_true",
        help="Only list application environments",
    )

    delete_parser = subparsers.add_parser(
        "delete_env",
        help="Delete a specific environment by name",
    )

    delete_parser.add_argument(
        "environment_name",
        help="Name of the environment to delete",
    )

    return parser


def get_columns(
    *,
    data: Iterable,
    headings: list[str],
    attributes: list[str],
    getter: Callable[[object, str], str] = getattr,
) -> Generator[str]:
    """
    A helper function to generate a table to print with correct column widths

    :param data: input data
    :param headings: headings for the top of the table
    :param attributes: attribute names to use for each column
    :param getter: attribute getter function (ex: getattr, dict.get)
    :return: Generator of column lines
    """
    if len(headings) != len(attributes):
        raise TypeError("Must be the same number of headings as attributes")

    widths = {
        f"{attrib}": len(head) for attrib, head in zip(attributes, headings)
    }

    data_rows = []
    for d in data:
        row = []
        for attrib in attributes:
            d_text = f"{getter(d, attrib)}"
            d_len = len(d_text)
            widths[f"{attrib}"] = max(widths[attrib], d_len)
            row.append(d_text)
        data_rows.append(row)

    yield (
        "| "
        + " | ".join(f"{head:<{widths[attrib]}}"
                     for head, attrib in zip(headings, attributes))
        + " |"
    )
    yield (
        "| "
        + " | ".join("-" * widths[attrib]
                     for attrib in attributes)
        + " |"
    )

    for row in data_rows:
        yield (
            "| "
            + " | ".join(f"{item:<{widths[attrib]}}"
                         for item, attrib in zip(row, attributes))
            + " |"
        )


def main():
    parser = get_parser()
    args, unknown = parser.parse_known_args()

    if unknown:
        # "run" needs to be able to handle ambiguous arguments
        # ie: things that look like positional args should be passed on.
        # This should only be done for arguments placed *after* the script name
        if args.command == "run":
            raw_args = sys.argv[1:]
            _script_args = raw_args.index(args.script_filename) + 1
            new_args = [*raw_args[:_script_args], "--", *raw_args[_script_args:]]
            # re-parse
            args = parser.parse_args(new_args)
        else:
            unknown_s = " ".join(unknown)
            parser.error(f"unrecognised arguments: {unknown_s}")

    # Create a manager
    manager = _laz.Manager(PROJECT_NAME)

    if args.command == "run":
        spec = _laz.EnvironmentSpec.from_script(
            script_path=args.script_filename
        )
        if args.generate_lock:
            uv_path = manager.retrieve_uv(required=True)
            lockdata = spec.generate_lockdata(uv_path=uv_path)
            lock_path = f"{args.script_filename}.lock"
            with open(lock_path, 'w') as f:
                f.write(lockdata)
        elif lock_path := args.with_lock:
            with open(lock_path, 'r') as f:
                lockdata = f.read()
            spec.lockdata = lockdata

        manager.run_direct_script(
            spec=spec,
            args=args.script_args,
        )
    elif args.command == "bundle":
        spec = _laz.EnvironmentSpec.from_script(
            script_path=args.script_filename
        )
        
        if args.generate_lock:
            uv_path = manager.retrieve_uv(required=True)
            spec.generate_lockdata(uv_path=uv_path)
        elif lock_path := args.with_lock:
            with open(lock_path, 'r') as f:
                lockdata = f.read()
            spec.lockdata = lockdata

        manager.create_bundle(
            spec=spec,
            output_file=args.output,
        )
    elif args.command == "generate_lock":
        uv_path = manager.retrieve_uv(required=True)
        spec = _laz.EnvironmentSpec.from_script(
            script_path=args.script_filename
        )
        lockdata = spec.generate_lockdata(uv_path=uv_path)

        out_path = args.output if args.output else f"{args.script_filename}.lock"
        with open(out_path, "w") as f:
            f.write(lockdata)
    elif args.command == "clear_cache":
        if args.full:
            manager.clear_project_folder()
        else:
            manager.clear_temporary_cache()
    elif args.command == "rebuild_env":
        manager.build_env_folder()
        if args.zipapp:
            manager.build_zipapp()
    elif args.command == "list":
        has_envs = False
        if manager.temp_catalogue.environments and not args.app:
            has_envs = True
            print("Temporary Environments")
            print("======================")
            formatted = get_columns(
                data=manager.temp_catalogue.environments.values(),
                headings=["Name", "Last Used"],
                attributes=["name", "last_used_simple"]
            )
            for line in formatted:
                print(line)
            if not args.temp:
                print()

        if manager.app_catalogue.environments and not args.temp:
            has_envs = True
            print("Application environments")
            print("========================")
            formatted = get_columns(
                data=manager.app_catalogue.environments.values(),
                headings=["Owner / Name", "Last Used"],
                attributes=["name", "last_used_simple"]
            )
            for line in formatted:
                print(line)

        if has_envs is False:
            print("No environments managed by ducktools-env")
    elif args.command == "delete_env":
        envname = args.environment_name
        if envname in manager.temp_catalogue.environments:
            manager.temp_catalogue.delete_env(envname)
            print(f"Temporary environment {envname!r} deleted")
        elif envname in manager.app_catalogue.environments:
            manager.app_catalogue.delete_env(envname)
            print(f"Application environment {envname!r} deleted")
        else:
            print(f"Environment {envname!r} not found")
    else:
        # Should be unreachable
        raise ValueError("Invalid command")


if __name__ == "__main__":
    main()
