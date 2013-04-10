#!/usr/bin/env python
# -*- coding: utf-8 -*-

__author__ = 'Michael Liao'

'''
A WSGI application.
'''

import os, logging

from transwarp import web, db, cache

from auth import load_user

def create_app(debug):
    # init db:
    db.init(db_type='mysql', db_schema='shici', \
        db_host='localhost', db_port=3306, \
        db_user='www-data', db_password='www-data', \
        use_unicode=True, charset='utf8')
    # init cache:
    cache.client = cache.MemcacheClient('localhost:11211')
    scan = ['apis']
    if debug:
        scan.append('static_handler')
    return web.WSGIApplication(scan, \
            document_root=os.path.dirname(os.path.abspath(__file__)), \
            template_engine='jinja2', \
            filters=(load_user,), \
            DEBUG=debug)
