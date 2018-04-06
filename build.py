from pybuilder.core import use_plugin, init

use_plugin("python.core")
use_plugin("python.unittest")
use_plugin("python.install_dependencies")
use_plugin("python.flake8")
use_plugin("python.coverage")
use_plugin("python.distutils")


name = "all_branches_cloner"
default_task = "publish"


@init
def set_properties(project):
    project.depends_on('requests')
    project.depends_on('gitpython')
    project.depends_on('logging')
    project.depends_on('pprint')
    project.depends_on('argparse')
    project.depends_on('logging')
