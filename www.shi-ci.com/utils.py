#!/usr/bin/env python
# -*- coding: utf-8 -*-

import logging
import web

__author__ = 'Michael Liao'

def _load_s2t():
    logging.info('Loading Chinese simplified->to->traditional table...')
    d = dict()
    for hz in web.ctx.db.select('hanz'):
        d[hz.s] = hz.t
    logging.info('Loaded %d characters.' % len(d))
    return d

_S2T_DICT = _load_s2t()

def s2t(uni_str):
    L = []
    for u in uni_str:
        L.append(_S2T_DICT.get(u, u))
    return u''.join(L)
