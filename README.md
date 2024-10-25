# DuckTools: Env #

`ducktools-env` intends to provide a few tools to aid in running and distributing
applications and scripts written in Python that require additional dependencies.

## What is this for? ##

Suppose you have a Python script that you wish to share with someone else, but 
it relies on a third party dependency such as `requests`. In order for someone else
to run your code they need to both have an appropriate version of Python
and to create a virtual environment in which to install `requests` and subsequently
run your script.

PEP-723 introduced 
[inline script metadata](https://packaging.python.org/en/latest/specifications/inline-script-metadata/#inline-script-metadata)
which allows users to declare dependencies for single python files in a standardized format.
This is designed to make sharing scripts with PyPI dependencies easier as now the script
can define its own requirements.

However, using this format requires the use of an extra package such as 'UV' or 'hatch'
using a specific command such as `uv run my_script.py` or `hatch run my_script.py`.

`ducktools-env` is designed to bundle your script into a Python 
[zipapp](https://docs.python.org/3/library/zipapp.html) which can be run by any 
Python 3.10+ install and will handle creating the virtualenv and launching the script
with the appropriate dependencies *without* needing the other user to have any
specific script running tool installed.

To aid this, `ducktools-env` provides the `bundle` and `run` commands.

`ducktools-env run my_script.py`

Will run your script much like some of the other script runners.

`ducktools-env bundle my_script.py`

Will then generate a zipapp bundle of your script and the required tools to extract and
execute it in the same way as it is executed via the `run` command.

The resulting bundle will include `ducktools-env` and the `pip` zipapp in order to 
bootstrap the unbundling process. `UV` will be downloaded and installed on unbundling 
if it is available (on PyPI) for the platform.

## What if the user does not have Python installed ##

Running the bundle requires the user to have an install of Python 3.10 or later.
This should be available via python.org with installers for Windows/Mac and either
already included or available from any up to date Linux distribution. This is all
that should be needed for your script to run.

The version of Python that will actually be used to build the environment will be the latest
version that can be found via [ducktools-pythonfinder](https://github.com/DavidCEllis/ducktools-pythonfinder)
that satisfies the `requires-python` specification.

If no version can be found `ducktools-env` will try to use `UV` to install an appropriate
version automatically and use that to build the environment.

## Where is data stored? ##

Environment data and the application itself will be stored in the following locations:

* Windows: `%LOCALAPPDATA%\ducktools\env`
* Linux/Mac/Other: `~/.ducktools/env`

## Usage ##

The tool can be used in multiple ways:

* Installed via `uv tool` (or `pipx`)
  * `uv tool install ducktools-env`
  * `ducktools-env <command>`
  * This adds the `dtrun` shortcut for `ducktools-env run`
* Executed from the zipapp
  * Download from: https://github.com/DavidCEllis/ducktools-env/releases/latest
  * Run with: `ducktools.pyz <command>`
* Installed in an environment
  * Download with `pip` or `uv` in a virtual environment: `pip install ducktools-env`
  * Run with: `ducktools-env <command>`
* Accessed directly via `uvx` with uv
  * `uvx ducktools-env <command>`

These examples will use the `ducktools-env` command as the base as if installed via `uv tool` or a similar tool.

Run a script that uses inline script metadata:

`ducktools-env run my_script.py`

If installed via `uv`, `pipx` or `pip` there is an alias `dtrun` for this command. 
Unlike the full command it does not accept optional arguments and all arguments are passed
on to the script.

`dtrun my_script.py`

Bundle the script into a zipapp:

`ducktools-env bundle my_script.py`

Clear the temporary environment cache:

`ducktools-env clear_cache`

Clear the full `ducktools/env` install directory:

`ducktools-env clear_cache --full`

Build the env folder from the installed package:

`ducktools-env rebuild_env`

### Registering scripts ###

It is also now possible to register scripts with `ducktools-env`.

`ducktools-env register path/to/my_script.py`

which can then be run by using the script name without the extension:

`ducktools-env run my_script` or `dtrun my_script`

## Locking environments ##

When generating zipapp bundles it may be desirable to also generate a lockfile
to make sure that the versions of installed dependencies do not change between 
generation and execution without having to over specify in the original
script.

This generation feature uses `uv` which will be automatically installed.
`uv` is **not** required to use the generated lockfile (but will usually be installed).

Create a lockfile without running a script:

`ducktools-env generate_lock my_script.py`

Run a script and output the generated lockfile (output as my_script.py.lock):

`ducktools-env run --generate-lock my_script.py` (--generate-lock does not work with `dtrun`)

Run a script using a pre-generated lockfile:

`ducktools-env run --with-lock my_script.py.lock my_script.py`

**If a `my_script.py.lock` file is found for a script it will automatically be used without
needing to be specified**

Bundle a script and generate a lockfile (that will be bundled):

`ducktools-env bundle --generate-lock my_script.py`

Bundle a script with a pre-generated lockfile:

`ducktools-env bundle --with-lock my_script.py.lock my_script.py`

**If a `my_script.py.lock` file exists it will automatically be used.**

## Including data files with script bundles ##

If you wish to include data files with your script you can do so using a tool
table in the toml block.

```python
# /// script
# requires-python = ">=3.10"
# dependencies = ["cowsay"]
# 
# [tool.ducktools.env]
# include.data = ["path/to/folder", "path/to/file.txt"]
# ///
```

If this is made into a bundle these files and folders will be collected into a bundle_data folder
included in the zipapp.

This data can be retrieved on demand using `get_data_folder` from `ducktools.env.bundled_data` which
will create a temporary folder containing a copy of the data files and return the path to the folder.

Note: Paths are relative to the script folder. If you include a folder, the folder itself will be 
included, not just its contents. This means that if you include `./` you will get the name of the 
folder the script is in (along with all of its contents).

This can be used to include additional code by inserting the relevant folder into `sys.path` before
executing the body of a script.

```python
# /// script
# requires-python = ">=3.12"
# dependencies = ["ducktools-env>=0.1.0"]
# 
# [tool.ducktools.env]
# include.data = ["./"]
# include.license = ["license.md"]
# ///
from pathlib import Path

from ducktools.env.bundled_data import get_data_folder 

with get_data_folder() as fld_name:
    for f in Path(fld_name).rglob("*"):
        print(f)
```

## Application Environments ##

If you wish your script to persist as an "application" you can define 'owner', 'name' and 'version'
fields.

These environments **require** generation of a lockfile.

A new version of the application will update the environment to depend on that version. The environment
will be rebuilt if the lockfile is updated on updating to a new version. If the lockfile has changed
but the version has not, running the application will fail (unless the version is a pre-release). 
Old versions will also fail to run if the environment has been created for a new version.

```python
# /// script
# requires-python = ">=3.8.0"
# dependencies = ["cowsay"]
# [tool.ducktools.env]
# app.owner = "ducktools_testing"
# app.name = "cowsay_example"
# app.version = "0.1.0"
# ///

from cowsay.__main__ import cli

if __name__ == "__main__":
    cli()
```

## Listing and deleting environments ##

Existing environments can be listed with the command

`ducktools-env list`

and deleted with 

`ducktools-env delete_env <envname>`

where `<envname>` is the `name` of a temporary environment or the combination 
`owner/name` of an application environment as shown in the list.

## Goals ##

Future goals for this tool:

* Optionally bundle requirements inside the zipapp for use as offline bundles.

## Dependencies ##

Currently `ducktools.env` relies on the following tools.

Subprocesses:
* `venv` via subprocess on python installs where UV is unavailable
* `pip` as a zipapp via subprocess used to install UV and where UV is unavailable
* `uv` where available as a faster installer and for locking dependencies for bundles

PyPI: 
* `ducktools-classbuilder` (A lazy, faster implementation of the building blocks behind things like dataclasses)
* `ducktools-lazyimporter` (A simple class based tool to handle deferred imports)
* `ducktools-scriptmetadata` (The parser for inline script metadata blocks)
* `ducktools-pythonfinder` (A tool to discover python installs available for environment creation)
* `packaging` (for comparing dependency lists to cached environments)
* `tomli` (for Python 3.10 to support the TOML format)

## Other tools in this space ##

### zipapp ###

The standard library `zipapp` is at the core of how `ducktools-env` works. However it doesn't support
running with C extensions and it has no inbuilt way to control which Python it will run under.

By contrast `ducktools-env` will respect a specified python version and required extensions, these
can be bundled or downloaded on first launch via `pip`.

### Shiv ###

`shiv` allows you to bundle zipapps with C extensions, but doesn't provide for any `online` installs
and will extract everything into one `~/.shiv` directory unless otherwise specified. 
`ducktools-env` will create a separate environment for each unique set of requirements
for temporary environments by matching specification.

### PEX ###

`pex` provides an assortment of related tools for developers alongside a `.pex` bundler.
It doesn't (to my knowledge) have support for inline script metadata and it makes `.pex` files
instead of `.pyz` files.

### PyInstaller ###

Pyinstaller will generate an executable from your script but will also bundle all of your 
dependencies in a platform specific way. It also bundles Python itself, which while 
convenient if python is not installed, is unnecessary if we can treat Python as a shared
library.

### Hatch ###

`Hatch` allows you to run scripts with inline dependencies, but requires the user on the other end
already have hatch installed. The goal of `ducktools-env` is to make it so you can quickly bundle the script
into a zipapp that will work on the other end with only Python as the requirement.

### pipx ###

`pipx` is another tool that allows you to install packages from PyPI and run them as applications
based on their `[project.scripts]` and `[project.gui-scripts]`. This is different from `ducktools-env`
which specifically builds scripts into bundles based on inline dependencies.
