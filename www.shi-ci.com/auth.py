#!/usr/bin/env python
# -*- coding: utf-8 -*-

__author__ = 'Michael Liao'

'''
Make or validate cookie.
'''

import os, time, base64, hashlib, logging, functools

from transwarp.web import ctx, Dict
from transwarp import db

from config import SIGN_SALT

COOKIE_AUTH = 'auth'

def make_session_cookie(id, access_token, expires):
    '''
    >>> make_session_cookie('w1234', 'ToKen', 2365507832)
    'dzEyMzQ6MjM2NTUwNzgzMjoxYzM3YmJjZjJjZTUwMDU4N2U2Njc4MTI5NWFmNGMxNg=='
    '''
    md5 = hashlib.md5('%s:%s:%s:%s' % (str(id), expires, str(access_token), SIGN_SALT)).hexdigest()
    return base64.b64encode('%s:%s:%s' % (id, expires, md5))

def extract_session_cookie(cookie_str, fn_select_user):
    '''
    >>> fn = lambda uid: Dict(oauth_access_token='ToKen')
    >>> extract_session_cookie('dzEyMzQ6MjM2NTUwNzgzMjoxYzM3YmJjZjJjZTUwMDU4N2U2Njc4MTI5NWFmNGMxNg==', fn)
    {'oauth_access_token': 'ToKen'}
    '''
    logging.info('GET cookie: %s' % cookie_str)
    if not cookie_str:
        return None
    try:
        s = base64.b64decode(str(cookie_str))
    except BaseException:
        logging.info('Bad cookie: base64 decode error.')
        return None
    # type:id:expires:md5
    ss = s.split(':', 2)
    if len(ss)!=3:
        logging.info(r'Bad cookie: split ":" failed.')
        return None
    id = ss[0]
    try:
        expires = int(ss[1])
    except ValueError:
        logging.info('Bad cookie: invalid time.')
        return None
    if time.time() > expires:
        logging.info('Bad cookie: expired time.')
        return None
    md5 = str(ss[2])
    if len(md5) != 32:
        logging.info('Bad cookie: bad md5.')
        return None
    # check md5:
    user = fn_select_user(id)
    if user:
        if md5 != hashlib.md5('%s:%s:%s:%s' % (id, expires, str(user.oauth_access_token), SIGN_SALT)).hexdigest():
            logging.info('Bad cookie: invalid md5.')
            return None
        logging.info('Found user from cookie: id=%s' % id)
        return user
    logging.info('Bad cookie: user not found in db.')
    return None

def fn_load_user(uid):
    users = db.select('select * from user where id=?', uid)
    if users:
        return users[0]
    return None

def load_user(func):
    @functools.wraps(func)
    def _wrapper(*args, **kw):
        cookie_str = ctx.request.cookie(COOKIE_AUTH)
        user = None
        if cookie_str:
            user = extract_session_cookie(cookie_str, fn_load_user)
        ctx.user = user
        try:
            return func(*args, **kw)
        finally:
            del ctx.user
    return _wrapper

if __name__=='__main__':
    import doctest
    doctest.testmod()
 