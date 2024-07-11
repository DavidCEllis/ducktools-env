The current version of this was entirely designed around handling temporary venvs. 

I'd like to expand this to handle application venvs to aid with bundling applications as zipapps.

* [ ] Build script for stand-alone applications
* [ ] Bootstrap env function
* [ ] Main script for project builds/running script metadata functions
  * [ ] Separate projects/scripts - ducktools.run and ducktools.build
* [ ] Handle temporary virtual environments
* [ ] Handle application virtual environments
  * [ ] Allow users to install applications from PyPI
* [ ] Bundle support for downloading libraries from PyPI


Install  Options:
* [ ] Support for downloading dependencies from PyPI
  * [ ] Optional auto-updating based on config 
  * [ ] Hash checking for specific versions in secure installs
    * In this case updates will require a new archive 
* [ ] Support for bundling all dependencies
  * In this case updates will require a new archive
  * Separate and merged binaries for projects that have platform dependant builds


## Environment folder structure ##

* Base Folder
  * Windows: `%LOCALAPPDATA%\ducktools\environments`
  * Linux: `~/.ducktools/environments`
  * MacOS: `~/Library/Caches/ducktools/environments` <-- This may change
* Config File: `config_v<major_version>.json`
* Catalogue File: `catalogue_v<major_version>.json` inside each folder for ENVs
* Core environment: `/core_v<major_version>`
* Temporary VEnvs: `/temporary`
* Application VEnvs: `/application`


## What needs to happen on running a zipapp ##

* Check if there is already a core environment
* Check if the ducktools-envman version in that environment is >= the version bundled
* If it is newer - use that version instead of the bundled one for app building
* 