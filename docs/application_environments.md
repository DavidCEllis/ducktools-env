## Application Environments ##

Application environments can be declared by adding `owner`, `appname` and `version` fields to the 
`[tool.ducktools.env.app]`. Unlike temporary environments these will not expire automatically
or be removed when the cache size reaches a limit.

Application environments *MUST* use a lockfile.

If the spec hash matches an application environment it will automatically be used, if not the
owner, appname and version will be checked, a different owner/appname will not be considered the
same "application". 

If the version that is being run is older than the env version an error will be raised, 
if the version matches but the lock does not an error will be raised *UNLESS* both are 
pre-releases, in this case the environment will be rebuilt with the new lockfile.

If the version is newer and the lock does not match, the environment will be rebuilt
if the lock matches the environment will be kept, but the version number updated.
Old spec hashes will be cleared out when the version number is updated. 
