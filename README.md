# DuckTools: Env #

`ducktools-env` intends to provide a few tools to aid in running, testing and distributing
applications and scripts written in Python that require additional dependencies.

## Currently implemented ##

This pre-release version provides a way to run scripts based on
[inline script metadata](https://packaging.python.org/en/latest/specifications/inline-script-metadata/#inline-script-metadata)
and a second tool to bundle such scripts into python's 
[zipapp](https://docs.python.org/3/library/zipapp.html)
format in a way that can be run without needing to have `ducktools-env` already installed.

This works by creating temporary environments in the following folders:

* Windows: `%LOCALAPPDATA%\ducktools\environments`
* Linux: `~/.ducktools/environments`
* Mac: Unsure, currently not supported - possibly in `~/Library/Caches/ducktools/environments`?


## Goals ##

Future goals for this tool:

* Create 'permanent' named environments for stand-alone applications and update them
  * Currently all environments are in a kind of LRU cache and expire in a week (configurable)
* Bundle applications that are not single-file scripts based on some configuration format
  * Possibly waiting until PEP-751 has a resolution for lock files


  
## Dependencies ##

Currently `ducktools.env` relies on the following tools.

Subprocesses:
* `venv` (via subprocess on python installs)
  * (Might eventually use `virtualenv` as there are python installs without `venv`)
* `pip` (as a zipapp via subprocess within a venv)

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
`ducktools-env` will create a separate environment for each independent project, 
or for temporary environments by matching specification.

### PEX ###

`pex` provides an assortment of related tools for developers alongside a `.pex` bundler.
It doesn't (to my knowledge) have support for inline script metadata and it makes `.pex` files
instead of `.pyz` files.

## Why not use UV for dependency management? ##

UV is new and fast, but in order to make the install portable **without** always requiring 
an internet connection it would be necessary to bundle the binaries for UV for every 
platform, meaning 16 copies at over 200MB. Even then there may be platforms where someone
has built Python but not uv.

By relying on pure python dependencies only, `ducktools-env` should work anywhere that Python
works and does not require any additional compilation.
