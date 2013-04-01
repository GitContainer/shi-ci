#!/usr/bin/env python
# -*- coding: utf-8 -*-

__author__ = 'Michael Liao'

try:
    import json
except ImportError:
    import simplejson as json
import time
import random
import hashlib
import logging
import datetime

from lunar import get_lunar_date
from weibo import APIClient, _encode_params

from framework import cache, Page, next_id, handler, create_oauth_cookie, COOKIE_NAME, COOKIE_EXPIRES

import web

################################################################################
# private constants                                                            #
################################################################################

_SIGN_SALT = '#WWW-ShiCi-zh#'

_SHI_CI_ID = 'weibo_1926704223'

_APP_KEY = '2370412278'
_APP_SECRET = '1509cfa7864a37b9471bc25d377a7cc8'
_CALLBACK = 'http://www.shi-ci.com/auth_callback2'

_PAGE_SIZE = 20

################################################################################
# private functions                                                            #
################################################################################

@cache(10800)
def _get_featured_poems():
    total = web.ctx.db.query('select count(id) as num from poem where ilike>=100')[0].num
    s = set()
    while len(s)<5:
        s.add(random.randint(0, total-1))
    L1 = [web.ctx.db.query('select * from poem where ilike>=100 order by id limit $first, $max', vars={'first':n, 'max':1})[0] for n in s]
    total = web.ctx.db.query('select count(id) as num from poem where ilike<100')[0].num
    s = set()
    while len(s)<5:
        s.add(random.randint(0, total-1))
    L2 = [web.ctx.db.query('select * from poem where ilike<100 order by id limit $first, $max', vars={'first':n, 'max':1})[0] for n in s]
    L1.extend(L2)
    return L1

def _get_oauth_id(user_id):
    n = user_id.find(u'_')
    if n!=(-1):
        return user_id[n+1:]
    return user_id

def _get_poem_weibo_id(poem):
    wid = poem.weibo_id
    if not wid:
        wid = _post_poem(poem)
        web.ctx.db.update('poem', where='id=$id', vars=dict(id=poem.id), weibo_id=wid)
    return wid

def _post_poem(poem):
    ' post poem to weibo using official account '
    users = list(web.ctx.db.select('user', where='id=$id', vars=dict(id=_SHI_CI_ID)))
    if not users:
        raise StandardError('official user not found.')
    user = users[0]
    client = APIClient(_APP_KEY, _APP_SECRET, _CALLBACK)
    client.set_access_token(user.oauth_access_token, user.oauth_expires)
    url_long = 'http://www.shi-ci.com/poem/%s' % poem.id
    urls = client.short_url__shorten(url_long=url_long)
    logging.info('short_url/shorten result: %s' % str(urls))
    url_short = urls['urls'][0]['url_short']
    head = u'%s(%s)：' % (poem.name, poem.poet_name)
    if poem.poet_name==u'毛泽东':
        head = u'%s：' % poem.name
    body_left = (280 - 2 - len(url_short) - 2 * len(head)) // 2
    if len(poem.content) <= body_left:
        text = u'%s%s %s' % (head, poem.content, url_short)
    else:
        text = u'%s%s... %s' % (head, poem.content[:body_left-2], url_short)
    r = client.post.statuses__update(status=text)
    logging.info('statuses/update result: %s' % str(r))
    return r['id']

def _get_referer():
    '''
    Get referer url for redirecting after signin.
    '''
    referer = web.ctx.env.get('HTTP_REFERER', '/')
    if referer.startswith('http') and not referer.startswith('http://www.shi-ci.com/'):
        return '/'
    if referer.find('auth_') != (-1):
        return '/'
    return referer

def _load_poet_comments(poet_id):
    '''
    Load comments of a poet.
    '''
    comments = list(web.ctx.db.select('poem_comment', where='poet_id=$pid', vars=dict(pid=poet_id), limit=5, order='creation_time desc'))
    for c in comments:
        L = list(web.ctx.db.select('poem', where='id=$id', vars=dict(id=c.poem_id)))
        if L:
            c.poem = L[0]
        else:
            c.poem = None
    return comments

def _load_poem_comments(poem_id):
    '''
    Load comments of a poem.
    '''
    comments = list(web.ctx.db.select('poem_comment', where='poem_id=$pid', vars=dict(pid=poem_id), limit=5, order='creation_time desc'))
    for c in comments:
        c.poem = None
    return comments

@cache(600)
def _load_recent_comments():
    '''
    Load recent comments.
    '''
    comments = list(web.ctx.db.select('poem_comment', limit=5, order='creation_time desc'))
    for c in comments:
        L = list(web.ctx.db.select('poem', where='id=$id', vars=dict(id=c.poem_id)))
        if L:
            c.poem = L[0]
        else:
            c.poem = None
    return comments

def _get_page(str, total_items, pagesize=_PAGE_SIZE):
    '''
    Get page object.
    '''
    p = 1
    try:
        p = int(str)
    except ValueError:
        raise web.notfound('invalid page')
    return Page(total_items, p, pagesize)

@cache(36000)
def _load_dynasty():
    return list(web.ctx.db.select('dynasty', order='display_order'))

@cache(36000)
def _load_category():
    return list(web.ctx.db.select('category', order='display_order'))

def _init_dict(**kw):
    d = dict(**kw)
    d['user'] = web.ctx.user
    d['dynasties'] = _load_dynasty()
    d['categories'] = _load_category()
    return d

################################################################################
# url functions                                                                #
################################################################################

def check_admin():
    if web.ctx.user:
        if web.ctx.user.admin:
            return
    raise web.forbidden()

@handler('GET')
def admin_set_famous(poem_id):
    check_admin()
    web.ctx.db.update('poem', where='id=$id', vars=dict(id=poem_id), ilike=random.randint(100,1000))
    return '200 OK'

@handler('GET')
def admin_will_add_poem():
    check_admin()
    return _init_dict(title="ADD", locations=(), comments=())

@handler('POST')
def admin_add_poem():
    check_admin()
    import utils
    i = web.input()
    poet_id = i.poet_id
    poet = list(web.ctx.db.select('poet', where='id=$id', vars=dict(id=poet_id)))[0]
    t = int(time.time())
    d = dict(
            poet_id = poet.id, \
            poet_name = poet.name, \
            poet_name_cht = poet.name_cht, \
            poet_name_pinyin = poet.pinyin, \
            dynasty_id = poet.dynasty_id, \
            dynasty_name = poet.dynasty_name, \
            dynasty_name_cht = poet.dynasty_name_cht, \
            weibo_id = '', \
            weibo_cht_id = '', \
            form = int(i.form), \
            name = i.name, \
            name_cht = utils.s2t(i.name), \
            name_pinyin = i.name_pinyin, \
            content = i.content, \
            content_cht = utils.s2t(i.content), \
            content_pinyin = i.content_pinyin, \
            visit_count = 0, \
            comment_count = 0, \
            has_audio = 0, \
            has_video = 0, \
            ilike = 0, \
            idislike = 0, \
            version = t, \
            id=str(t))
    web.ctx.db.insert('poem', **d)
    raise web.found('/poem/%s' % d['id'])

@handler('GET')
def admin_edit_poem(id):
    check_admin()
    L = list(web.ctx.db.select('poem', where='id=$id', vars=dict(id=id)))
    return _init_dict(title="EDIT", locations=(), comments=(), poem=L[0])

@handler('POST')
def admin_update_poem():
    check_admin()
    import utils
    i = web.input()
    id = i.id
    name = i.name.replace(u'\n', u'').replace(u'\r', u'')
    content = i.content.replace(u'\n', u'').replace(u'\r', u'')
    name_pinyin = i.name_pinyin
    content_pinyin = i.content_pinyin
    name_cht = utils.s2t(name)
    content_cht = utils.s2t(content)
    ilike = int(i.ilike)
    form = int(i.form)
    web.ctx.db.update('poem', where='id=$id', vars=dict(id=id), ilike=ilike, form=form, name=name, name_cht=name_cht, name_pinyin=name_pinyin, content=content, content_cht=content_cht, content_pinyin=content_pinyin, version=int(time.time()))
    raise web.found('/poem/%s' % id)

@handler('GET')
def test():
    '''
    Test page
    '''
    return _init_dict(title=u'测试页', locations=((u'中华诗词', '/'), (u'测试页', None),), comments=_load_recent_comments())

@handler('GET')
def support():
    '''
    GET /support
    
    Show help page.
    '''
    return _init_dict(title=u'帮助', locations=((u'中华诗词', '/'), (u'帮助', None),), comments=())

@handler('GET')
def index():
    '''
    GET /
    
    Show index page.
    '''
    return _init_dict(title=u'首页', locations=((u'中华诗词', '/'), (u'首页', None),), featured=_get_featured_poems(), comments=_load_recent_comments())

@handler('GET')
def search():
    i = web.input(q=u'', dynasty=u'', form=u'', category=u'')
    return _init_dict(title=u'搜索结果', locations=((u'中华诗词', '/'), (u'搜索结果', None),), q=i.q, q_dynasty=i.dynasty, q_form=i.form, q_category=i.category, comments=_load_recent_comments())

@handler('GET')
def dynasty(id, ps='1'):
    '''
    GET /dynasty/{dynasty_id}/{page}
    
    Show dynasty page.
    '''
    L = list(web.ctx.db.select('dynasty', where='id=$id', vars=dict(id=id)))
    if not L:
        raise web.notfound('invalid dynasty')
    dynasty = L[0]
    p = _get_page(ps, dynasty.poet_count)
    poets = list(web.ctx.db.select('poet', where='dynasty_id=$id', vars=dict(id=id), order='name', limit=p.__limit__, offset=p.__offset__))
    return _init_dict(title=dynasty.name, locations=((u'中华诗词', '/'), (dynasty.name, None),), dynasty=dynasty, page=p, poets=poets, comments=_load_recent_comments())

@handler('GET')
def poet(id, ps='1'):
    '''
    GET /poet/{poet_id}/{page}
    
    Show poet page.
    '''
    L = list(web.ctx.db.select('poet', where='id=$id', vars=dict(id=id)))
    if not L:
        raise web.notfound('no such poet')
    poet = L[0]

    p = _get_page(ps, poet.poem_count)
    poems = list(web.ctx.db.select('poem', where='poet_id=$id', vars=dict(id=id), limit=p.__limit__, offset=p.__offset__, order='name_pinyin'))
    locations = ( \
            (u'中华诗词', '/'), \
            (poet.dynasty_name, '/dynasty/%s' % poet.dynasty_id), \
            (poet.name, None),)
    return _init_dict(title=poet.name, locations=locations, poet=poet, page=p, poems=poems, comments=_load_poet_comments(id))

@handler('GET')
def auth_failed():
    return _init_dict(title=u'登录失败', locations=((u'中华诗词', '/'), (u'登录失败', None),))

@handler('GET')
def poem(id):
    '''
    GET /poem/{poem_id}
    
    Show poem page.
    '''
    L = list(web.ctx.db.select('poem', where='id=$id', vars=dict(id=id)))
    if not L:
        raise web.notfound('no such poem')
    poem = L[0]
    locations = ( \
            (u'中华诗词', '/'), \
            (poem.dynasty_name, '/dynasty/%s' % poem.dynasty_id), \
            (poem.poet_name, '/poet/%s' % poem.poet_id), \
            (poem.name, None),)
    return _init_dict(title=poem.name, locations=locations, poem=poem, comments=_load_poem_comments(id))

def _posted_before(now, dt):
    delta = now - dt
    return delta.days * 86400 + delta.seconds

@handler('GET')
def m_poem_comments(id, ps='1'):
    '''
    GET /m_poem_comments/{poem_id}/{page}
    '''
    page = int(ps)
    if page<1 or page>100:
        return r'{"error":"invalid_page","description":"invalid page."}'
    page_size = 20
    offset = page_size * (page - 1)
    L = list(web.ctx.db.select('poem', where='id=$id', vars=dict(id=id)))
    if not L:
        return r'{"error":"not_found","description":"poem not found."}'
    poem = L[0]
    comments = list(web.ctx.db.select('poem_comment', where='poem_id=$pid', vars=dict(pid=id), offset=offset, limit=page_size+1, order='creation_time desc'))
    has_next = len(comments) > page_size
    if has_next:
        comments = comments[:-1]
    now = datetime.datetime.now()
    return json.dumps(dict(
            page = page, \
            next = has_next, \
            time = time.time(), \
            comments = [dict(user_name=c.user_name, user_image=c.user_image, user_url=c.user_url, content=c.content, posted_before=_posted_before(now, c.creation_time)) for c in comments] \
    ))

def _comment():
    '''
    Make a comment on a poem by reposting it as a tweet.
    
    Returns:
        json string.
    '''
    web.header('Content-Type', 'application/json')
    user = web.ctx.user
    if user is None:
        return r'{"error":"auth_failed","description":"登录已失效，请<a href=\"/auth_signin\" rel=\"nofollow\">重新登录</a>！"}'
    i = web.input(statuses=u'', id=u'')
    text = i.statuses.strip().replace(u'\r\n', u' ').replace(u'\n', u' ').replace(u'\r', u' ')
    if not text or not i.id:
        return '{"error":"input_error","description":"输入错误！"}'
    poem = list(web.ctx.db.select('poem', where='id=$id', vars=dict(id=i.id)))[0]
    wid = _get_poem_weibo_id(poem)
    # repost it:
    client = APIClient(_APP_KEY, _APP_SECRET, _CALLBACK)
    client.set_access_token(user.oauth_access_token, user.oauth_expires)
    r = client.post.statuses__repost(id=wid, status=i.statuses, is_comment=1)
    rid = r['id']
    url = 'http://api.t.sina.com.cn/%s/statuses/%s' % (_get_oauth_id(user.id), rid)
    web.ctx.db.insert('poem_comment', \
            id = next_id(), \
            user_id = user.id, \
            user_name = user.name, \
            user_url = user.oauth_url, \
            user_image = user.oauth_image, \
            poem_id = poem.id, \
            poem_name = poem.name, \
            poet_id = poem.poet_id, \
            ref_url = url, \
            content = text)
    web.ctx.db.query('update poem set comment_count=comment_count+1 where id=$id', vars=dict(id=i.id))
    return json.dumps(dict(id=rid, url=url))

@handler('POST')
def comment():
    return _comment()

@handler('POST')
def m_comment():
    return _comment()

@handler('GET')
def auth_signout():
    '''
    Sign out and redirect to previous page.
    '''
    web.setcookie(COOKIE_NAME, 'deleted', -360000)
    web.seeother(_get_referer())

@handler('GET')
def auth_signin():
    '''
    Redirect to sina sign in page.
    '''
    client = APIClient(app_key=_APP_KEY, app_secret=_APP_SECRET, redirect_uri=_CALLBACK)
    raise web.seeother(client.get_authorize_url())

def _user_info_after_oauth(client, access_token, expires, uid):
    client.set_access_token(access_token, expires)
    account = client.users__show(uid=uid)
    image = account.get(u'profile_image_url', u'about:blank')
    logging.info('got account: %s' % str(account))
    name = account.get('screen_name', u'') or account.get('name', u'')

    id = u'weibo_%s' % uid
    users = list(web.ctx.db.select('user', where='id=$id', vars=dict(id=id)))
    if users:
        user = users[0]
        # update user if necessary:
        web.ctx.db.update('user', where='id=$id', vars=dict(id=id), \
                name = name, \
                oauth_image = image, \
                oauth_access_token = access_token, \
                oauth_expires = expires)
    else:
        web.ctx.db.insert('user', \
                id = id, \
                name = name, \
                oauth_access_token = access_token, \
                oauth_expires = expires, \
                oauth_url = u'http://weibo.com/u/%s' % uid, \
                oauth_image = image, \
                admin = False)
    # make a signin cookie:
    cookie_str = create_oauth_cookie(id, access_token, expires)
    logging.info('will set cookie: %s' % cookie_str)
    return dict(cookie=cookie_str, id=id, name=name, image=image)

@handler('GET')
def auth_callback2():
    '''
    Callback from sina, then redirect to previous url.
    '''
    i = web.input(code=u'')
    if not i.code:
        raise web.seeother('/auth_failed')
    client = APIClient(app_key=_APP_KEY, app_secret=_APP_SECRET, redirect_uri=_CALLBACK)
    r = client.request_access_token(i.code)
    access_token = r.access_token
    expires_in = r.expires_in
    uid = r.uid
    info = _user_info_after_oauth(client, access_token, expires_in, uid)
    # make a signin cookie:
    web.setcookie(COOKIE_NAME, info['cookie'], expires_in - int(time.time()) - 600)
    raise web.seeother('http://www.shi-ci.com/')

@handler('GET', 'application/json')
def m_poem(id):
    '''
    GET /m_poem/{poem_id}
    
    Returns:
        Poem json.
    '''
    _check_sign('m_poem', str(id))
    L = list(web.ctx.db.select('poem', where='id=$id', vars=dict(id=id)))
    if not L:
        return '{"error":"not_found"}'
    p = L[0]
    d = dict(**p)
    del d['weibo_id']
    del d['weibo_cht_id']
    return json.dumps(d)

@handler('GET', 'application/json')
@cache(10800)
def m_featured():
    _check_sign('m_featured')
    ps = _get_featured_poems()
    return json.dumps(dict(poems=ps))

@handler('GET', 'application/json')
def m_favorites():
    _check_sign('m_favorites')
    return json.dumps(dict(poems=[]))

@handler('GET', 'application/json')
def m_categories():
    _check_sign('m_categories')
    cats = _load_category()
    return json.dumps(dict(categories=cats))

@handler('GET', 'application/json')
@cache(36000)
def m_category(id):
    _check_sign('m_category')
    poems = list(web.ctx.db.query('select p.* from category_poem cp inner join poem p on cp.poem_id=p.id where cp.category_id=$id', vars=dict(id=id)))
    return json.dumps(dict(poems=poems))

def _share(id):
    '''
    share poem and return the weibo url after share.
    '''
    web.header('Content-Type', 'application/json')
    user = web.ctx.user
    if user is None:
        return '{"error":"auth_failed"}'
    poem = list(web.ctx.db.select('poem', where='id=$id', vars=dict(id=id)))[0]
    wid = _get_poem_weibo_id(poem)
    # share it:
    client = APIClient(_APP_KEY, _APP_SECRET, _CALLBACK)
    client.set_access_token(user.oauth_access_token, user.oauth_expires)
    r = client.post.statuses__repost(id=wid, status=u'分享诗词：%s' % poem.name)
    rid = r['id']
    redirect = 'http://api.t.sina.com.cn/%s/statuses/%s' % (_get_oauth_id(user.id), rid)
    return '{"url":"%s"}' % redirect

@handler('GET')
def share(id):
    '''
    GET /share/{poem_id}
    
    Returns:
        json contains url.
    '''
    return _share(id)

@handler('GET')
def m_share(id):
    '''
    GET /m_share/{poem_id}

    Returns:
        json contains url.
    '''
    return _share(id)

@handler('POST')
def auth_mobile_signin():
    '''
    POST /auth_mobile_signin
    
    email=xxx@example.com&passwd=PASSWORD
    
    Returns:
        json string contains access token.
    '''
    web.header('Content-Type', 'application/json')
    i = web.input(email=u'', passwd=u'')
    email = i.email
    passwd = i.passwd
    if not email or not passwd:
        return r'{"error":"missing_param"}'
    client = APIClient(_APP_KEY, _APP_SECRET, callback=_CALLBACK)
    t = client.get_request_token()

    oauth_token = t.oauth_token
    oauth_token_secret = t.oauth_token_secret

    logging.info('oauth_token = %s' % t.oauth_token)
    logging.info('oauth_token_secret = %s' % t.oauth_token_secret)

    url = client.get_authorize_url(t.oauth_token)
    logging.info('GET authorize url: %s' % url)

    import httplib
    headers = {
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10.6) Firefox/8.0.1',
            'Content-Type': 'application/x-www-form-urlencoded',
            'Referer': 'http://www.shi-ci.com/auth_signin'
    }
    conn = httplib.HTTPConnection('api.t.sina.com.cn')
    conn.request('GET', '/oauth/authorize?oauth_token=%s' % oauth_token, headers=headers)
    resp = conn.getresponse()
    if resp.status!=200:
        logging.info('Failed to get oauth/authorize.')
        return r'{"error":"auth_failed"}'
    body = resp.read()
    INPUT_VERIFY_TOKEN = r'<input type="hidden" name="verifyToken" value="'
    n1 = body.find(INPUT_VERIFY_TOKEN)
    if n1==(-1):
        logging.info('Failed to find verifyToken.')
        return r'{"error":"auth_failed"}'
    n2 = body.find(r'"/>', n1)
    if n2==(-1):
        logging.info('Failed to find verifyToken.')
        return r'{"error":"auth_failed"}'
    verifyToken = body[n1+len(INPUT_VERIFY_TOKEN):n2]
    logging.info('Find verifyToken: %s' % verifyToken)

    data = {
            'action': 'submit',
            'forcelogin': '',
            'from': '',
            'oauth_callback': _CALLBACK,
            'oauth_token': oauth_token,
            'verifyToken': verifyToken,
            'userId': email,
            'passwd': passwd,
            'regCallback': 'http://api.t.sina.com.cn/oauth/authorize?oauth_token=%s&oauth_callback=%s&from=&with_cookie=' % (oauth_token, _CALLBACK),
    }
    headers = {
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10.6) Firefox/8.0.1',
            'Content-Type': 'application/x-www-form-urlencoded',
            'Referer': 'http://api.t.sina.com.cn/oauth/authorize?oauth_token=%s' % oauth_token,
    }
    print _encode_params(**data)
    conn = httplib.HTTPConnection('api.t.sina.com.cn')
    conn.request('POST', '/oauth/authorize', body=_encode_params(**data), headers=headers)
    resp = conn.getresponse()
    if resp.status!=302:
        return r'{"error":"auth_failed"}'
    location = resp.getheader('Location')
    logging.info('Got redirect location: %s' % location)
    query = location[location.find('?')+1:]
    access_token = APIClient(_APP_KEY, _APP_SECRET, token=t2).get_access_token()

    info = _user_info_after_oauth(access_token)
    return json.dumps(info)

def _check_sign(*args):
    if True:
        return
    actual = str(web.input(sign='').sign)
    if len(actual)==32:
        L = [_SIGN_SALT]
        L.extend(args)
        expected = hashlib.md5(''.join(L)).hexdigest()
        if expected==actual:
            return
        logging.warn('bad sign: expected %s but %s' % (expected, actual))
    raise web.forbidden('bad signature')
