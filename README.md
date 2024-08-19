# DuckTools: Env #

`ducktools-env` intends to provide a few tools to aid in running and distributing
applications and scripts written in Python that require additional dependencies.

## Goals ##

Provide a way to easily create executable zipapps from scripts with inline dependencies
or wheels with entry points.

The zipapps created are self installing bundles that can download and install dependencies
from PyPI into managed virtual environments.

## Currently implemented ##

This pre-release version provides a way to run scripts based on
[inline script metadata](https://packaging.python.org/en/latest/specifications/inline-script-metadata/#inline-script-metadata)
and a second tool to bundle such scripts into python's 
[zipapp](https://docs.python.org/3/library/zipapp.html)
format in a way that can be run without needing to have `ducktools-env` already installed.

This works by creating temporary environments in the following folders:

* Windows: `%LOCALAPPDATA%\ducktools\environments`
* Linux/Mac/Other: `~/.ducktools/environments`

## What it does ##

When you run a script with ducktools-env it will look at the inline dependencies.

It will use [ducktools-pythonfinder](https://github.com/DavidCEllis/ducktools-pythonfinder) to attempt
to find the newest valid python install (not a venv) that satisfies any python requirement.

Having done that it will create a temporary venv with any dependencies listed and execute the script in the
venv.

## Usage ##

Either install the tool from PyPI or simply download the zipapp from github.

Run a script that uses inline script metadata:
`python ducktools.pyz run my_script.py`

Bundle the script into a zipapp:
`python ducktools.pyz bundle my_script.py`

Clear the temporary environment cache:
`python ducktools.pyz clear_cache`

Re-install the cached ducktools-env
`python ducktools.pyz rebuild_env`

## Goals ##

Future goals for this tool:

* Generate lockfiles for bundled apps so dependencies can be restricted.
* Bundle requirements inside the zipapp for use without a connection.
* Bundle applications that are wheels with a `__main__.py` function.
* Create 'permanent' named environments for stand-alone applications and update them
  * Currently there is a maximum of 2 temporary environments that expire in a day
    (this is due to the pre-release nature of the project, the future defaults will be higher/longer)

## Dependencies ##

Currently `ducktools.env` relies on the following tools.

Subprocesses:
* `venv` (via subprocess on python installs)
  * (Might eventually use `virtualenv` as there are python installs without `venv`)
* `pip` (as a zipapp via subprocess)

PyPI: 
* `ducktools-classbuilder` (A lazy, faster implementation of the building blocks behind things like dataclasses)
* `ducktools-lazyimporter` (A simple class based tool to handle deferred imports)
* `ducktools-scriptmetadata` (The parser for inline script metadata blocks)
* `ducktools-pythonfinder` (A tool to discover python installs available for environment creation)
* `packaging` (for comparing dependency lists to cached environments)
* `tomli` (for Python 3.10 and earlier to support the TOML format)
* `importlib-resources` (to handle finding file paths correctly when building bundles)
* `zipp`  (To handle path-like objects in zips in older python correctly)

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

### Hatch ###

`Hatch` allows you to run scripts with inline dependencies, but requires the user on the other end
already have hatch installed. The goal of `ducktools-env` is to make it so you can quickly bundle the script
into a zipapp that will work on the other end with only Python as the requirement.

### pipx ###

`pipx` is another tool that allows you to install packages from PyPI and run them as applications
based on their `[project.scripts]` and `[project.gui-scripts]`. This is a goal of ducktools.env, 
except it would build separate zipapps for each script and the apps would share the same cached 
python environment.

## UV ##

UV may be used in the future as a potential performance boost and to generate lockfiles for
bundled environments. However, it will not replace `pip` as the primary installer as one goal 
is that bundled scripts created using this will run anywhere Python can run.
