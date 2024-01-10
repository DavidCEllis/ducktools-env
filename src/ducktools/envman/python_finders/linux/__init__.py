from .pyenv_search import get_pyenv_pythons
from .dist_python_search import get_dist_pythons


def get_python_installs():
    return [*get_pyenv_pythons(), *get_dist_pythons()]
