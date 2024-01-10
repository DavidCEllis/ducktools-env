# DuckTools: EnvMan #

EnvMan is a toolkit for managing python environments from python. This is designed to be
a backend for tools intended to handle environment management for users.

## Dependencies ##

Currently ducktools.envman relies on the following tools.

Subprocesses:
* `venv` (via subprocess on python installs)
* `pip` (via subprocess within a venv)
* `pyenv` (one option for finding python installs)

PyPI: 
* `prefab-classes` (A lazy implementation of dataclasses)
* `ducktools-lazyimporter`
* `ducktools-scriptmetadata`
* `packaging`
* `tomli` (for Python 3.10)
