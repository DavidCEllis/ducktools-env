# DuckTools: EnvMan #

EnvMan is a toolkit for managing temporary python virtual environments.

## Dependencies ##

Currently ducktools.envman relies on the following tools.

Subprocesses:
* `venv` (via subprocess on python installs)
* `pip` (via subprocess within a venv)

PyPI: 
* `prefab-classes` (A lazy, faster implementation of the same concept as dataclasses)
* `ducktools-lazyimporter`
* `ducktools-scriptmetadata`
* `ducktools-pythonfinder`
* `packaging`
* `tomli` (for Python 3.10)
