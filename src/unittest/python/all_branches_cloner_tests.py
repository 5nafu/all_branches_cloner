#!/usr/bin/env python

#from mockito import mock, verify
import unittest
import logging

from all_branches_cloner import CloneAllBranches


class CloneAllBranchesTest(unittest.TestCase):
    def test_can_be_initialized(self):
        abc = CloneAllBranches(
            'myserver',
            'testproject',
            'testrepo',
            'targetdirectory',
            'testuser',
            'testpassword',
            logging.INFO,
        )
