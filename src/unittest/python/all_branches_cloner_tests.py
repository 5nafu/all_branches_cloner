#!/usr/bin/env python

# from mockito import mock, verify
from testfixtures import log_capture
import unittest
import logging

from all_branches_cloner import CloneAllBranches


class CloneAllBranchesTest(unittest.TestCase):
    @log_capture()
    def test_can_be_initialized(self, capture):
        abc = CloneAllBranches(
            'myserver',
            'testproject',
            'testrepo',
            'targetdirectory',
            'testuser',
            'testpassword',
            logging.INFO,
        )
        self.assertNotIn('testpassword', capture.records[-1].getMessage())
        self.assertIn('testuser', capture.records[-1].getMessage())
