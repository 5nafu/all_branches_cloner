#!/usr/bin/env python

import sys
from os.path import join

source_path = join("src", "main", "python")
script_path = join("src", "main", "scripts", "all_branches_cloner")

sys.path.insert(0, source_path)
exec(open(script_path, 'r').read())
