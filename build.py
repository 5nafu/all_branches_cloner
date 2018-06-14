from pybuilder.core import use_plugin, init, Author

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


@init
def set_properties(project):
    project.depends_on('requests')
    project.depends_on('gitpython')
    project.build_depends_on('testfixtures')
    project.build_depends_on('responses')
    project.build_depends_on('mock')
