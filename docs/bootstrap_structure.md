# Bootstrap project structures #

## Online Bootstrap ##

```
__main__.py
ducktools/env/... <- Full ducktools env folder - could be reduced in future

instructions.json <- Build instructions/environment settings
app.py <- Generated application script that will be called
```



## Offline Bootstrap ##

```
__main__.py
ducktools/env/... <-- Full ducktools env folder

wheels/... <-- all dependencies from pip freeze as wheels

instructions.json <-- includes instruction not to update from online
app.py
```