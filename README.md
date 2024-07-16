# DuckTools: Env #

ducktools-env handles automatically creating Python environments for applications and scripts.

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
* `packaging` (for comparing dependency lists to cached environments)
* `tomli` (for Python 3.10)
