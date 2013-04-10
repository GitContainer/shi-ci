#!/usr/bin/env python
# -*- coding: utf-8 -*-

__author__ = 'Michael Liao'

'''
A WSGI application in production mode.
'''

import wsgi

application = wsgi.create_app(debug=False)
