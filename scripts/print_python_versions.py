from ducktools.envman.python_finders.pyenv_finder import get_pyenv_versions
from ducktools.envman.python_finders.syspython_unix import get_system_python_installs

for env in get_pyenv_versions():
    print(env)
