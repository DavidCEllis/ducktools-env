# DuckTools: EnvMan #

EnvMan is a library that provides a basic toolkit for managing temporary python 
virtual environments.

## Usage ##

Launching a python with matching python version and environment.

```python
import subprocess
import datetime
from ducktools.envman import Config, Catalogue, EnvironmentSpec

script_path = "path/to/script.py"

# Make a catalogue with a 1 day cache life
config = Config(cache_expires=datetime.timedelta(days=1))
catalogue = Catalogue.from_config(config)

spec = EnvironmentSpec.from_file(script_path)

# Find or Build a python environment that satisfies the inline dependency requirements
python_env = catalogue.find_or_create_env(spec)

# Run the script in the specified environment
subprocess.run([python_env.python_path, script_path])
```

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
