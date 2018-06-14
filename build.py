import subprocess
import os
from pybuilder.core import use_plugin, init, Author, task, description, depends

use_plugin("python.core")
use_plugin("python.unittest")
use_plugin("python.install_dependencies")
use_plugin("python.flake8")
use_plugin("python.coverage")
use_plugin("python.distutils")


name = "all-branches-cloner"
license = 'GNU GPL v3'
version = "1.1"
summary = "Clones all open branches from a bitbucket server"
default_task = ["install_dependencies", "publish"]
authors = [Author("Tobias Vollmer", "info@tvollmer.de")]


@task
@depends("publish")
@description("Creates a debian package")
def create_deb(project, logger):
    command = [
        "/usr/local/bin/fpm",
        "-a", "all",                                                     # Architecture
        "-s", "python",                                                  # Source Type
        "-t", "deb",                                                     # Package Type
        "-p", "target/dist",                                             # Output directory
        "--python-install-bin", "/usr/bin",                              # Script install dir
        "--python-scripts-executable", "/usr/bin/python",                # Script install dir
        "--python-install-lib", "/usr/lib/python2.7/dist-packages",      # Module install dir
        "--python-scripts-executable", "/usr/bin/python",                # Python Executable
        "--python-bin", "/usr/bin/python",                               # Python Executable
        "--no-auto-depends",                                             # Dont manage dependencies
        "--name", project.name,                                          # Package Name
        "--description", project.summary,                                # Description
        "--version", project.version,                                    # Version
        "--maintainer", project.authors[0].email,                        # Maintainer Email
        "-d", "python-requests",                                         # Dependency
        "-d", "python-git",                                              # Dependency
        "target/dist/%s-%s/setup.py" % (project.name, project.version)  # Source directory
    ]
    if not os.path.isfile(command[0]):
        raise IOError("Could not find executable %s" % command[0])
    subprocess.check_call(command)

@init
def set_properties(project):
    project.depends_on('requests')
    project.depends_on('gitpython')
    project.build_depends_on('testfixtures')
    project.build_depends_on('responses')
    project.build_depends_on('mock')
