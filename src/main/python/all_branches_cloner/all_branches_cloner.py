#!/usr/bin/env python

import requests
import os
import git
import logging
import shutil


class CloneAllBranches(object):
    def __init__(self, server, project, repo, target, user, password, loglevel, symlinks={}, keep=[], logger=None):
        self.project = project
        self.repo = repo
        self.server = server
        self.target = target
        self.symlinks = symlinks
        self.keep_environments = keep
        self.user = user
        self.password = password
        self.open_branches = []
        logging.basicConfig(level=loglevel)
        self.logger = logger or logging.getLogger(__name__)
        self.logger.info('CloneAllBranches initialized with options:')
        options = dict(vars(self))
        options['password'] = '********' if options['password'] else options['password']
        self.logger.info(options)


    def __sanitize_name(self, name):
        return name.replace('/', '___')

    def get_all_branch_info(self):
        self.logger.info('STARTING - getting all branches')
        repourl = 'https://%s/rest/api/1.0/projects/%s/repos/%s/branches?details=true&start=%s'
        metadata = []
        lastpage = False
        start = 0

        while not lastpage:
            url = repourl % (self.server, self.project, self.repo, start)
            self.logger.info('Requesting: "%s"' % url)
            request = requests.get(url, auth=(self.user, self.password))
            json = request.json()
            metadata.extend(json['values'])
            lastpage = json['isLastPage']
            self.logger.info('Got isLastPage: %s' % lastpage)
            if not lastpage:
                start = json['nextPageStart']
        self.logger.info('Got %i branches' % len(metadata))
        self.logger.info('FINISHED - getting all branches')
        return metadata

    def get_open_branch_names(self, all_branches):
        self.logger.info('STARTING - getting open branches')
        open_branches = []
        provider = 'com.atlassian.bitbucket.server.bitbucket-branch:ahead-behind-metadata-provider'
        for branch in all_branches:
            if branch['metadata'].get(provider) and branch['metadata'][provider]['ahead'] > 0:
                self.logger.info('Found open branch "%s" (%i commits ahead)' % (branch['displayId'], branch['metadata'][provider]['ahead']))
                open_branches.append(branch['displayId'])
        self.logger.info('FINISHED - getting open branches')
        return open_branches

    def remove_obsolete_branches(self):
        self.logger.info('STARTING - removing old branches')
        all_cloned_branches = [name for name in os.listdir(self.target) if os.path.isdir(os.path.join(self.target, name))]
        sanitized_open_branches = [self.__sanitize_name(branch) for branch in self.open_branches]
        for branch in all_cloned_branches:
            if branch in sanitized_open_branches:
                self.logger.info('Not removing branch "%s" -> still open' % branch)
            elif branch in self.keep_environments:
                self.logger.info('Not removing branch "%s" -> excluded' % branch)
            elif os.path.islink(os.path.join(self.target, branch)):
                self.logger.info('Not removing branch "%s" -> is a symlink' % branch)
            else:
                self.logger.info('Removing branch "%s"' % branch)
                shutil.rmtree(os.path.join(self.target, branch))
        self.logger.info('FINISHED - removing old branches')

    def update_or_clone_open_branches(self):
        self.logger.info('STARTING - updating / cloning open branches')
        git_url = 'ssh://git@%s:7999/%s/%s.git' % (self.server, self.project, self.repo)
        self.logger.info('Fetching from "%s"' % git_url)
        for branch in self.open_branches:
            directory = os.path.join(self.target, self.__sanitize_name(branch))
            if os.path.isdir(directory):
                self.logger.info('Branch "%s" exists - pulling from remote' % branch)
                git.Git(directory).pull()
            else:
                self.logger.info('Branch "%s" does not exist - cloning' % branch)
                git.Git().clone(git_url, directory, depth=1, branch=branch)
            if self.symlinks:
                self.logger.info('Generating symlinks:')
                for symlink in self.symlinks.keys():
                    if not os.path.exists(os.path.join(directory, symlink)):
                        self.logger.info('generating link: %s -> %s' % (self.symlinks[symlink], os.path.join(branch, symlink)))
                        os.symlink(self.symlinks[symlink], os.path.join(directory, symlink))
                    else:
                        self.logger.info('link "%s" already exists' % os.path.join(branch, symlink))
        self.logger.info('FINISHED - updating / cloning open branches')

    def create_clones(self):
        all_branches = self.get_all_branch_info()
        self.open_branches = self.get_open_branch_names(all_branches)
        self.remove_obsolete_branches()
        self.update_or_clone_open_branches()
