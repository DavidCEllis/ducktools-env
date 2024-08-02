The current version of this was entirely designed around handling temporary venvs. 

## Environment folder structure ##

* Base Folder
  * Windows: `%LOCALAPPDATA%\ducktools\environments`
  * Linux: `~/.ducktools/environments`
  * MacOS: `~/Library/Caches/ducktools/environments` <-- This may change

* Manager folder: `/libs`
* Manager zipapp: `ducktools-env.pyz`
* Manager Contents:
  * Version File: `ENV_VERSION`


* Config File: `config.json`
* Catalogue File: `catalogue.json` inside each folder for ENVs
* Temporary VEnvs: `/caches`
* Application VEnvs: `/application`


## Config Options ##

Various install options:

update_frequency: "daily", "weekly", "fortnightly", "never" (Default - "daily")
only_binary: (:all: by default)

offline_install: "True" - bundle all dependencies into the pyz for supported platforms


## What needs to happen on running a zipapp ##

Metadata Requirements:
```
[tool.ducktools.env]
project.name = "ducktools_env"  # Overrides project.name in pyproject.toml
project.version = "v0.0.1"  # Overrides version in pyproject.toml
project.owner = "davidcellis"
```

* Check if there is already a core environment
* Update the core environment from PyPI if it is outdated (check once daily at most)
* Update the core environment from a bundle if a newer version is included
* Use the core environment that is already installed if it is newer than the bundled version

* Launch the application if the environment already exists
* Create a venv and install all dependencies and launch the command provided


## Multi-project structure ##

ducktools.env.run: script launcher - has main
ducktools.env.bundle: zipapp maker - has main


## Bootstrap logic ##

* `__main__.py` runs `bootstrap.py` to get the path to the ducktools-env executable.
* `__main__.py` launches `app.py` using the ducktools-env executable.

### `bootstrap.py` ###

Checks if 

Return path to the core python executable



