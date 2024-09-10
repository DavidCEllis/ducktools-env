# DuckTools: Env #

`ducktools-env` intends to provide a few tools to aid in running and distributing
applications and scripts written in Python that require additional dependencies.

## What is this for? ##

*Or: uv/hatch/pipx already exist, why are you creating yet another packaging tool?*

PEP-723 introduced 
[inline script metadata](https://packaging.python.org/en/latest/specifications/inline-script-metadata/#inline-script-metadata)
which allows users to declare dependencies for single python files in a standardized format.

Using this format requires the use of an extra package such as 'UV' or 'hatch'
using a specific command such as `uv run my_script.py` or `hatch run my_script.py`.

`ducktools.env` provides a similar command 
`python ducktools.pyz run my_script.py` or `python -m ducktools.env run my_script.py`.

The problem that `ducktools.env` seeks to solve is what if you want to share your 
script or application with someone **who doesn't already have** `uv` or `hatch` or 
any other script runner that recognises this format.

To aid this, `ducktools.env` provides the `bundle` command.

`python ducktools.pyz bundle my_script.py`

This will generate a [zipapp](https://docs.python.org/3/library/zipapp.html) from your script
that will automatically extract and run it in the same way as with the `run` command.

This bundle will include `ducktools-env` and the `pip` zipapp in order to bootstrap the unbundling
process. `UV` will be downloaded and installed on unbundling if it is available (on PyPI) 
for the platform.

Environment data and the application itself will be stored in the following locations:

* Windows: `%LOCALAPPDATA%\ducktools\env`
* Linux/Mac/Other: `~/.ducktools/env`

## Discovering Python Installs ##

When you run a script with ducktools-env it will look at the inline dependencies.

It will use [ducktools-pythonfinder](https://github.com/DavidCEllis/ducktools-pythonfinder) to attempt
to find the newest valid python install (not a venv) that satisfies any python requirement. See its own 
page for which python installs it can find.

## Usage ##

Either install the tool from PyPI or simply download the zipapp from github.

If using the tool from PyPI the commands are `python -m ducktools.env <command>` 
with the zipapp they are `python ducktools.pyz <command>` 

Run a script that uses inline script metadata:
`python ducktools.pyz run my_script.py`

Bundle the script into a zipapp:
`python ducktools.pyz bundle my_script.py`

Clear the temporary environment cache:
`python ducktools.pyz clear_cache`

Clear the full `ducktools/env` install directory:
`python ducktools.pyz clear_cache --full`

Build the env folder from the installed package
**Generally you should not need to do this from the zipapp**
`python -m ducktools.env rebuild_env`

## Locking environments ##

When generating zipapp bundles it may be desirable to also generate a lockfile
to make sure that the versions of installed dependencies do not change between 
generation and execution without having to over specify in the original
script.

This generation feature uses `uv` which will be automatically installed.
`uv` is **not** required to use the generated lockfile (but will usually be installed).

Create a lockfile without running a script
`python ducktools.pyz generate_lock my_script.py`

Run a script and output the generated lockfile (output as my_script.py.lock)
`python ducktools.pyz run --generate-lock my_script.py`

Run a script using a pre-generated lockfile
`python ducktools.pyz run --with-lock my_script.py.lock my_script.py`

Bundle a script and generate a lockfile (that will be bundled)
`python ducktools.pyz bundle --generate-lock my_script.py`

Bundle a script with a pre-generated lockfile
`python ducktools.pyz bundle --with-lock my_script.py.lock my_script.py`


## Including data files with script bundles ##

If you wish to include data files with your script you can do so using a tool
table in the toml block.

```python
# /// script
# requires-python = ">=3.10"
# dependencies = ["cowsay"]
# 
# [tool.ducktools.env]
# bundle.data = ["path/to/folder", "path/to/file.txt"]
# ///
```

If this is made into a bundle these files and folders will be collected into a bundle_data folder
included in the zipapp.

This data can be retrieved on demand using `get_data_folder` from `ducktools.env.bundled_data` which
will create a temporary folder containing a copy of the data files and return the path to the folder.

Note: Paths are relative to the script folder. If you include a folder, the folder itself will be 
included, not just its contents. This means that if you include `./` you will get the name of the 
folder the script is in (along with all of its contents).

```python
# /// script
# requires-python = ">=3.12"
# dependencies = ["ducktools-env>=0.1.0"]
# 
# [tool.ducktools.env]
# bundle.data = ["./"]
# ///
from pathlib import Path

from ducktools.env.bundled_data import get_data_folder 

with get_data_folder() as fld_name:
    for f in Path(fld_name).rglob("*"):
        print(f)
```

## Goals ##

Future goals for this tool:

* Optionally bundle requirements inside the zipapp for use without a connection.
* Allow bundling of local wheel files unavailable on PyPI
* Create 'permanent' named environments for stand-alone applications and update them
  * Currently there is a maximum of 2 temporary environments that expire in a day
    (this is due to the pre-release nature of the project, the future defaults will be higher/longer)
* Automatically install required Python if UV is available

## Dependencies ##

Currently `ducktools.env` relies on the following tools.

Subprocesses:
* `venv` (via subprocess on python installs)
  * (Might eventually use `virtualenv` as there are python installs without `venv`)
* `pip` (as a zipapp via subprocess)
* `uv` where available as a faster installer and for locking dependencies for bundles

PyPI: 
* `ducktools-classbuilder` (A lazy, faster implementation of the building blocks behind things like dataclasses)
* `ducktools-lazyimporter` (A simple class based tool to handle deferred imports)
* `ducktools-scriptmetadata` (The parser for inline script metadata blocks)
* `ducktools-pythonfinder` (A tool to discover python installs available for environment creation)
* `packaging` (for comparing dependency lists to cached environments)
* `tomli` (for Python 3.10 and earlier to support the TOML format)

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
based on their `[project.scripts]` and `[project.gui-scripts]`. This is a goal of ducktools.env, 
except it would build separate zipapps for each script and the apps would share the same cached 
python environment.
