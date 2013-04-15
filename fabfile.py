#!/usr/bin/env python
# -*- coding: utf-8 -*-

__author__ = 'Michael Liao'

'''
Remote management.
'''

import os

from datetime import datetime
from fabric.api import *

env.user = 'root'
env.hosts = ['a.shi-ci.com']

def _current_path():
    return os.path.abspath('.')

#####################
# search.shi-ci.com #
#####################

_SEARCH_TAR_FILE = 'search.shi-ci.com.tar.gz'

def build_search():
    lpath = os.path.join(_current_path(), 'search.shi-ci.com', 'web')
    lfile = os.path.join(_current_path(), _SEARCH_TAR_FILE)
    with lcd(lpath):
        local('rm -f %s' % lfile)
        local('tar --dereference -czvf %s WEB-INF' % lfile)

_REMOTE_SEARCH_TMP_TAR = '/tmp/%s' % _SEARCH_TAR_FILE
_REMOTE_SEARCH_DIST_LINK = '/srv/search.shi-ci.com/www'
_REMOTE_SEARCH_DIST_DIR = '/srv/search.shi-ci.com/www-%s' % datetime.now().strftime('%y-%m-%d_%H.%M.%S')

def scp_search():
    run('rm -f %s' % _REMOTE_SEARCH_TMP_TAR)
    put(os.path.join(_current_path(), _SEARCH_TAR_FILE), _REMOTE_SEARCH_TMP_TAR)
    run('mkdir %s' % _REMOTE_SEARCH_DIST_DIR)
    with cd(_REMOTE_SEARCH_DIST_DIR):
        run('tar -xzvf %s' % _REMOTE_SEARCH_TMP_TAR)
    run('chown -R jetty:jetty %s' % _REMOTE_SEARCH_DIST_DIR)
    run('rm -f %s' % _REMOTE_SEARCH_DIST_LINK)
    run('ln -s %s %s' % (_REMOTE_SEARCH_DIST_DIR, _REMOTE_SEARCH_DIST_LINK))
    run('chown jetty:jetty %s' % _REMOTE_SEARCH_DIST_LINK)
    with settings(warn_only=True):
        run('/etc/init.d/jetty stop')
        run('/etc/init.d/jetty start')

##################
# www.shi-ci.com #
##################

_WWW_TAR_FILE = 'www.shi-ci.com.tar.gz'

def build_www():
    def _exclude(fname):
        return fname.startswith('.') or fname.endswith('.pyc') or fname.endswith('.pyo') or fname.endswith('.gz')
    lpath = os.path.join(_current_path(), 'www.shi-ci.com')
    lfile = os.path.join(_current_path(), _WWW_TAR_FILE)
    with lcd(lpath):
        files = os.listdir(lpath)
        includes = [f for f in files if not _exclude(f)]
        excludes = ['.*', '*.pyc', '*.pyo', '*.psd']
        local('rm -f %s' % lfile)
        cmd = ['tar', '--dereference', '-czvf', lfile]
        cmd.extend(['--exclude=\'%s\'' % ex for ex in excludes])
        cmd.extend(includes)
        local(' '.join(cmd))

_REMOTE_WWW_TMP_TAR = '/tmp/%s' % _WWW_TAR_FILE
_REMOTE_WWW_DIST_LINK = '/srv/www.shi-ci.com/www'
_REMOTE_WWW_DIST_DIR = '/srv/www.shi-ci.com/www-%s' % datetime.now().strftime('%y-%m-%d_%H.%M.%S')

def scp_www():
    run('rm -f %s' % _REMOTE_WWW_TMP_TAR)
    put(os.path.join(_current_path(), _WWW_TAR_FILE), _REMOTE_WWW_TMP_TAR)
    run('mkdir %s' % _REMOTE_WWW_DIST_DIR)
    with cd(_REMOTE_WWW_DIST_DIR):
        run('tar -xzvf %s' % _REMOTE_WWW_TMP_TAR)
    run('chown -R www-data:www-data %s' % _REMOTE_WWW_DIST_DIR)
    run('rm -f %s' % _REMOTE_WWW_DIST_LINK)
    run('ln -s %s %s' % (_REMOTE_WWW_DIST_DIR, _REMOTE_WWW_DIST_LINK))
    run('chown www-data:www-data %s' % _REMOTE_WWW_DIST_LINK)
    with settings(warn_only=True):
        run('supervisorctl stop shici')
        run('supervisorctl start shici')
