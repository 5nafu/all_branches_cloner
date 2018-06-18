#!/usr/bin/env python

# from mockito import mock, verify
from testfixtures import log_capture
import responses
import unittest
import mock
import logging
import os.path

from all_branches_cloner import CloneAllBranches


class CloneAllBranchesTest(unittest.TestCase):
    def setUp(self):
        self.host = 'myserver'
        self.project = 'testproject'
        self.repo = 'testrepo'
        self.directory = 'targetdirectory'
        self.user = 'testuser'
        self.password = 'testpassword'
        self.cloner = CloneAllBranches(
            self.host,
            self.project,
            self.repo,
            self.directory,
            self.user,
            self.password,
            logging.INFO,
        )

    @log_capture()
    def test_can_be_initialized(self, capture):
        CloneAllBranches(
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

    @responses.activate
    def test_get_all_branch_info_calls_only_once_on_single_page(self):
        testurl = 'https://%s/rest/api/1.0/projects/%s/repos/%s/branches?details=true&start=0' % (
            self.host,
            self.project,
            self.repo)
        testdata = [{
            'id': 'refs/heads/master',
            'displayId': 'master',
            'type': 'BRANCH',
            'latestCommit': 'c2f29994eb3499ac32d79b1bd6d398abaf1cd27a',
            'latestChangeset': 'c2f29994eb3415ac32d79b1bd6d398abaf1cd27a',
            'isDefault': True,
            'metadata': {
                'com.atlassian.bitbucket.server.bitbucket-jira:branch-list-jira-issues': [],
                'com.atlassian.bitbucket.server.bitbucket-branch:latest-commit-metadata': {
                    'id': 'c2f29994eb3415ac32d79b1bd6d398abaf1cd27a',
                    'displayId': 'c2f29994eb3',
                    'author': {
                        'name': 'Tester',
                        'emailAddress': 'tester@test.invalid'},
                    'authorTimestamp': 1527863276000,
                    'message': 'Commit Message',
                    'parents': [{
                        'id': '1a4e156ffd62f0eea520c995f68143a3e2f53913',
                        'displayId': '1a412345fd6'
                    }]
                }
            }
        }]
        responses.add(responses.GET, testurl, json={'values': testdata, 'isLastPage': 'true'}, status=200)
        metadata = self.cloner.get_all_branch_info()
        assert len(responses.calls) == 1
        self.assertEqual(metadata, testdata)

    @responses.activate
    def test_get_all_branch_info_calls_until_lastpage(self):
        testurl = 'https://%s/rest/api/1.0/projects/%s/repos/%s/branches' % (
            self.host,
            self.project,
            self.repo)
        testdata = ['branchone', 'branchtwo', 'branchthree']
        responses.add(responses.GET, testurl, json={'values': testdata, 'isLastPage': False, 'nextPageStart': 25}, status=200)
        responses.add(responses.GET, testurl, json={'values': testdata, 'isLastPage': True}, status=200)
        self.cloner.get_all_branch_info()
        self.assertEqual(responses.calls[1].response.url, testurl + '?details=true&start=25')
        assert len(responses.calls) == 2

    def test_get_open_branch_names_returns_empty_list(self):
        testdata = [{
            'id': 'refs/heads/master',
            'displayId': 'master',
            'metadata': {
                'com.atlassian.bitbucket.server.bitbucket-branch:latest-commit-metadata': {
                    'id': 'c2f29994eb3415ac32d79b1bd6d398abaf1cd27a',
                    'displayId': 'c2f29994eb3',
                }
            }
        }]
        self.assertEqual(len(self.cloner.get_open_branch_names(testdata)), 0)

    def test_get_open_branch_names_doesnt_return_master(self):
        testdata = [
            {
                'id': 'refs/heads/master',
                'displayId': 'master',
                'metadata': {
                    'com.atlassian.bitbucket.server.bitbucket-branch:latest-commit-metadata': {
                        'id': 'c2f29994eb3415ac32d79b1bd6d398abaf1cd27a',
                        'displayId': 'c2f29994eb3',
                    }
                }
            },
            {
                'id': 'refs/heads/testbranch_behind',
                'displayId': 'testbranch_behind',
                'metadata': {
                    'com.atlassian.bitbucket.server.bitbucket-branch:ahead-behind-metadata-provider': {
                        'ahead': 0,
                        'behind': 502
                    },
                    'com.atlassian.bitbucket.server.bitbucket-branch:latest-commit-metadata': {
                        'displayId': '5a13f762956',
                        'id': '5a13f7629560579275ae7b8427a14c62fa161338',
                    },
                },
                'type': 'BRANCH'
            },
            {
                'id': 'refs/heads/testbranch_ahead1',
                'displayId': 'testbranch_ahead1',
                'metadata': {
                    'com.atlassian.bitbucket.server.bitbucket-branch:ahead-behind-metadata-provider': {
                        'ahead': 123,
                        'behind': 502
                    },
                    'com.atlassian.bitbucket.server.bitbucket-branch:latest-commit-metadata': {
                        'displayId': '5a13f762956',
                        'id': '5a13f7629560579275ae7b8427a14c62fa161338',
                    },
                },
                'type': 'BRANCH'
            },
            {
                'id': 'refs/heads/testbranch_ahead2',
                'displayId': 'testbranch_ahead2',
                'metadata': {
                    'com.atlassian.bitbucket.server.bitbucket-branch:ahead-behind-metadata-provider': {
                        'ahead': 456,
                        'behind': 502
                    },
                    'com.atlassian.bitbucket.server.bitbucket-branch:latest-commit-metadata': {
                        'displayId': '5a13f762956',
                        'id': '5a13f7629560579275ae7b8427a14c62fa161338',
                    },
                },
                'type': 'BRANCH'
            }

        ]
        branches = self.cloner.get_open_branch_names(testdata)
        self.assertEqual(len(branches), 2)
        self.assertNotIn('testbranch_behind', branches)
        self.assertNotIn('master', branches)
        self.assertIn('testbranch_ahead1', branches)
        self.assertIn('testbranch_ahead2', branches)

    @mock.patch('all_branches_cloner.all_branches_cloner.os.path')
    @mock.patch('all_branches_cloner.all_branches_cloner.os')
    @mock.patch('all_branches_cloner.all_branches_cloner.shutil')
    def test_remove_obsolete_branches_no_removing_only_files(self, shutil_mock, os_mock, path_mock):
        self.cloner.open_branches = []
        os_mock.listdir.return_value = ['file1', 'file2', 'file3']
        path_mock.isdir.return_value = False
        path_mock.islink.return_value = False
        self.cloner.remove_obsolete_branches()
        os_mock.listdir.assert_called_with(self.directory)
        assert not shutil_mock.rmtree.called, 'rmtree should not have been called'

    @mock.patch('all_branches_cloner.all_branches_cloner.os.path')
    @mock.patch('all_branches_cloner.all_branches_cloner.os')
    @mock.patch('all_branches_cloner.all_branches_cloner.shutil')
    def test_remove_obsolete_branches_no_removing_symlink(self, shutil_mock, os_mock, path_mock):
        self.cloner.open_branches = []
        os_mock.listdir.return_value = ['symlink']
        path_mock.isdir.return_value = True
        path_mock.islink.return_value = True
        self.cloner.remove_obsolete_branches()
        assert not shutil_mock.rmtree.called, 'rmtree should not have been called on symlink'

    @mock.patch('all_branches_cloner.all_branches_cloner.os.path')
    @mock.patch('all_branches_cloner.all_branches_cloner.os')
    @mock.patch('all_branches_cloner.all_branches_cloner.shutil')
    def test_remove_obsolete_branches_no_removing_whitelisted(self, shutil_mock, os_mock, path_mock):
        self.cloner.open_branches = []
        self.cloner.keep_environments = ['whitelisted']
        os_mock.listdir.return_value = self.cloner.keep_environments
        path_mock.isdir.return_value = True
        path_mock.islink.return_value = False
        self.cloner.remove_obsolete_branches()
        assert not shutil_mock.rmtree.called, 'rmtree should not have been called on whitelisted'

    @mock.patch('all_branches_cloner.all_branches_cloner.os.path')
    @mock.patch('all_branches_cloner.all_branches_cloner.os')
    @mock.patch('all_branches_cloner.all_branches_cloner.shutil')
    def test_remove_obsolete_branches_no_removing_open(self, shutil_mock, os_mock, path_mock):
        self.cloner.open_branches = ['open']
        os_mock.listdir.return_value = self.cloner.open_branches
        path_mock.isdir.return_value = True
        path_mock.islink.return_value = False
        self.cloner.remove_obsolete_branches()
        assert not shutil_mock.rmtree.called, 'rmtree should not have been called on open branch'

    @mock.patch('all_branches_cloner.all_branches_cloner.os.path')
    @mock.patch('all_branches_cloner.all_branches_cloner.os')
    @mock.patch('all_branches_cloner.all_branches_cloner.shutil')
    def test_remove_obsolete_branches_no_removing_open_branch_with_slash(self, shutil_mock, os_mock, path_mock):
        self.cloner.open_branches = ['open/with_slash']
        os_mock.listdir.return_value = ['open___with_slash']
        path_mock.isdir.return_value = True
        path_mock.islink.return_value = False
        self.cloner.remove_obsolete_branches()
        assert not shutil_mock.rmtree.called, 'rmtree should not have been called on open branch with slash'

    @mock.patch('all_branches_cloner.all_branches_cloner.os.path')
    @mock.patch('all_branches_cloner.all_branches_cloner.os')
    @mock.patch('all_branches_cloner.all_branches_cloner.shutil')
    def test_remove_obsolete_branches_removes_merged_branch(self, shutil_mock, os_mock, path_mock):
        self.cloner.open_branches = []
        os_mock.listdir.return_value = ['merged']
        path_mock.isdir.return_value = True
        path_mock.islink.return_value = False
        path_mock.join.return_value = 'merged'
        self.cloner.remove_obsolete_branches()
        shutil_mock.rmtree.assert_called_with('merged')
        path_mock.join.assert_called_with(self.directory, 'merged')

    @mock.patch('all_branches_cloner.all_branches_cloner.git')
    @mock.patch('all_branches_cloner.all_branches_cloner.os.path')
    @mock.patch('all_branches_cloner.all_branches_cloner.os')
    def test_update_or_clone_open_branches_do_nothing_if_no_open(self, os_mock, path_mock, git_mock):
        self.cloner.open_branches = []
        git_mock.Git = mock.Mock()
        path_mock.isdir.return_value = True
        path_mock.join.return_value = 'branch'
        self.cloner.update_or_clone_open_branches()
        assert not git_mock.Git.called, 'Git should not have been called'

    @mock.patch('all_branches_cloner.all_branches_cloner.git')
    @mock.patch('all_branches_cloner.all_branches_cloner.os.path')
    @mock.patch('all_branches_cloner.all_branches_cloner.os')
    def test_update_or_clone_open_branches_pulls_existing_branch(self, os_mock, path_mock, git_mock):
        self.cloner.open_branches = ['existing_open_branch']
        git_mock.Git = mock.Mock()
        path_mock.isdir.return_value = True
        path_mock.join.return_value = 'existing_open_branch'
        self.cloner.update_or_clone_open_branches()
        git_mock.Git.assert_called_with('existing_open_branch')
        assert git_mock.Git('existing_open_branch').pull.called, 'Git pull should have been called'

    @mock.patch('all_branches_cloner.all_branches_cloner.git')
    @mock.patch('all_branches_cloner.all_branches_cloner.os.path')
    @mock.patch('all_branches_cloner.all_branches_cloner.os')
    def test_update_or_clone_open_branches_pulls_or_clones_branch_with_slash(self, os_mock, path_mock, git_mock):
        git_url = 'ssh://git@%s:7999/%s/%s.git' % (self.host, self.project, self.repo)
        self.cloner.open_branches = ['existing_open_branch/with_slash']
        target_dir = os.path.join(self.directory, self.cloner.open_branches[0])
        git_mock.Git = mock.Mock()
        path_mock.isdir.return_value = False
        path_mock.join.side_effect = os.path.join
        self.cloner.update_or_clone_open_branches()
        git_call = mock.call(
            git_url,
            target_dir,
            branch=self.cloner.open_branches[0],
            depth=1)
        self.assertNotIn(git_call, git_mock.Git().clone.call_args_list)

    @mock.patch('all_branches_cloner.all_branches_cloner.git')
    @mock.patch('all_branches_cloner.all_branches_cloner.os.path')
    @mock.patch('all_branches_cloner.all_branches_cloner.os')
    def test_update_or_clone_open_branches_clone_new_branch(self, os_mock, path_mock, git_mock):
        git_url = 'ssh://git@%s:7999/%s/%s.git' % (self.host, self.project, self.repo)
        target_dir = self.directory + '/new_open_branch'
        self.cloner.open_branches = ['new_open_branch']
        git_mock.Git = mock.Mock()
        path_mock.isdir.return_value = False
        path_mock.join.return_value = target_dir
        self.cloner.update_or_clone_open_branches()
        git_mock.Git.assert_called_with()
        git_mock.Git().clone.assert_called_with(git_url, target_dir, depth=1, branch='new_open_branch')

    @mock.patch('all_branches_cloner.all_branches_cloner.git')
    @mock.patch('all_branches_cloner.all_branches_cloner.os.path')
    @mock.patch('all_branches_cloner.all_branches_cloner.os')
    def test_update_or_clone_open_branches_dont_symlink_existing(self, os_mock, path_mock, git_mock):
        self.cloner.open_branches = ['open_branch1', 'open_branch2']
        self.cloner.symlinks = {'symlink1': 'target1', 'symlink2': 'target2'}
        path_mock.isdir.return_value = False
        path_mock.exists.return_value = True
        path_mock.join.side_effect = os.path.join
        self.cloner.update_or_clone_open_branches()
        assert not os_mock.symlink.called, 'Symlink should not be created'

    @mock.patch('all_branches_cloner.all_branches_cloner.git')
    @mock.patch('all_branches_cloner.all_branches_cloner.os.path')
    @mock.patch('all_branches_cloner.all_branches_cloner.os')
    def test_update_or_clone_open_branches_create_symlinks(self, os_mock, path_mock, git_mock):
        self.cloner.open_branches = ['open_branch1', 'open_branch2']
        self.cloner.symlinks = {'symlink1': 'target1', 'symlink2': 'target2'}
        path_mock.isdir.return_value = False
        path_mock.exists.return_value = False
        path_mock.join.side_effect = os.path.join
        self.cloner.update_or_clone_open_branches()
        calls = []
        for branch in self.cloner.open_branches:
            for symlink in self.cloner.symlinks.keys():
                calls.append(mock.call(self.cloner.symlinks[symlink], '/'.join([self.directory, branch, symlink])))
        os_mock.symlink.assert_has_calls(calls, any_order=True)
