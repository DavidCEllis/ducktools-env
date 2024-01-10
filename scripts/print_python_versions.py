from ducktools.envman.python_finders import get_python_installs

for env in get_python_installs():
    print(env)
