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

Possible options:
* [ ] Install required python versions automatically
  * I think for windows this could be done with the installers 

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


## Config Options ##

Various install options:
update_frequency: "daily", "weekly", "fortnightly", "monthly", "never" (Default - "daily")
package_index: link to alternate package index (default PyPI as pip) (URL)
only_binary: (:all: by default)

offline_install: "True" - bundle all dependencies into the pyz for supported platforms

include_pip: default to 'False', if 'True' then update pip on install
             In general packages require `pip` only as their installer but don't use it otherwise




## What needs to happen on running a zipapp ##

Metadata Requirements:
* Project Name
* Author Name
* Version Number


* Check if there is already a core environment
* Update the core environment from PyPI if it is outdated (check once daily at most)
* Update the core environment from a bundle if a newer version is included
* Use the core environment that is already installed if it is newer than the bundled version

* Launch the application if the environment already exists
* Create a venv and install all dependencies and launch the command provided
