#!/usr/bin/env python
# -*- coding: utf-8 -*-

__author__ = 'Michael Liao'

import json, time, random, urllib, hashlib, logging, datetime, functools
from datetime import datetime

from transwarp.web import ctx, get, post, notfound, seeother, Template
from transwarp import db, cache
from weibo import APIClient

import auth
import lunar

try:
    from config import SHI_CI_ID, APP_KEY, APP_SECRET
except ImportError:
    pass

COOKIE_REDIRECT = 'redirect'

CALLBACK = 'http://www.shi-ci.com/auth/callback'

PAGE_SIZE = 20

STATIC_PATH_PREFIX = ''

def cached(timeout=36000):
    def _decorator(func):
        @functools.wraps(func)
        def _wrapper(*args):
            key = 'SC_%s' % func.__name__
            if args:
                key = '%s_%s' % (key, ''.join(map(str, args)))
            r = cache.client.get(key)
            if r:
                logging.info('Hit cache!')
                return r
            logging.info('Not hit cache!')
            r = func(*args)
            cache.client.set(key, r, timeout)
            return r
        return _wrapper
    return _decorator

def template(path):
    def _decorator(func):
        @functools.wraps(func)
        def _wrapper(*args, **kw):
            r = func(*args, **kw)
            if isinstance(r, dict):
                y, m, d = get_today()
                r['__lunar_date__'] = get_lunar(y, m, d)
                r['__user__'] = ctx.user
                r['static_prefix'] = '' if ctx.application.debug else STATIC_PATH_PREFIX
                return Template('templates/%s' % path, r)
            return r
        return _wrapper
    return _decorator

def api(func):
    '''
    A decorator that makes a function to api, makes the return value as json.
    '''
    @functools.wraps(func)
    def _wrapper(*args, **kw):
        ctx.response.content_type = 'application/json; charset=utf-8'
        return json.dumps(func(*args, **kw))
    return _wrapper

def get_today():
    dt = datetime.now()
    return dt.year, dt.month, dt.day

def get_lunar(y, m, d):
    dt = datetime(y, m, d)
    ly, lm, ld, ll = lunar.get_lunar_date(dt)
    nm = lunar.name_of_month(lm, ll)
    nd = lunar.name_of_day(ld)
    jieqi = lunar.get_jieqi(y, m, d)
    if jieqi:
        return u'%s%s %s' % (nm, nd, jieqi)
    return u'%s%s' % (nm, nd)

@cached()
def get_dynasty(dyn_id):
    L = get_dynasties()
    for d in L:
        if d.id==dyn_id:
            return d
    raise notfound()

@cached()
def get_dynasties():
    return db.select('select * from dynasty order by display_order')

@cached()
def get_poet(poet_id):
    return db.select_one('select * from poet where id=?', poet_id)

@api
@cached()
@get('/m_featured')
def featured_poems():
    total = db.select_int('select count(id) as num from poem where ilike>=100')
    s = set()
    while len(s)<5:
        s.add(random.randint(0, total-1))
    L = []
    for n in s:
        L.extend(db.select('select * from poem where ilike>=100 order by id limit ?,?', n, 1))
    total = db.select_int('select count(id) from poem where ilike<100')
    s = set()
    while len(s)<5:
        s.add(random.randint(0, total-1))
    for n in s:
        L.extend(db.select('select * from poem where ilike<100 order by id limit ?,?', n, 1))
    return dict(poems=L)

@get('/')
@template('index.html')
def index_page():
    return dict(title=u'首页', dynasties=get_dynasties())

@get('/dynasty/<dyn_id>')
@template('dynasty.html')
def dynasty_page(dyn_id):
    '''
    GET /dynasty/{dynasty_id}/{page}
    
    Show dynasty page.
    '''
    dynasty = get_dynasty(dyn_id)
    dynasties = get_dynasties()
    poets = db.select('select * from poet where dynasty_id=? order by pinyin', dyn_id)
    return dict(title=dynasty.name, dynasty=dynasty, dynasties=dynasties, poets=poets)

def get_poems(poet_id, page=1):
    '''
    Return poems of page N (N=1, 2, 3) and has_next.
    '''
    if page < 1 or page > 100:
        raise ValueError('invalid page.')
    offset = PAGE_SIZE * (page - 1)
    maximum = PAGE_SIZE + 1
    L = db.select('select * from poem where poet_id=? order by name_pinyin limit ?,?', poet_id, offset, maximum)
    if len(L) == maximum:
        return L[:-1], True
    return L, False

@get('/poet/<poet_id>')
@template('poet.html')
def poet_page(poet_id):
    page = 1
    poet = get_poet(poet_id)
    dynasty = get_dynasty(poet.dynasty_id)
    dynasties = get_dynasties()
    poems, next = get_poems(poet_id, page)
    return dict(title=poet.name, dynasty=dynasty, dynasties=dynasties, poet=poet, poems=poems, page=page, next=next)

@api
@get('/more/poems')
def more_poems():
    i = ctx.request.input(poet_id='', page='')
    poems, next = get_poems(i.poet_id, int(i.page))
    return dict(poems=poems, next=next)

@cached()
def get_poem(poem_id):
    return db.select_one('select * from poem where id=?', poem_id)

@get('/poem/<poem_id>')
@template('poem.html')
def poem_page(poem_id):
    poem = get_poem(poem_id)
    poet = get_poet(poem.poet_id)
    dynasty = get_dynasty(poet.dynasty_id)
    dynasties = get_dynasties()
    return dict(title=poem.name, dynasties=dynasties, dynasty=dynasty, poet=poet, poem=poem)

@get('/auth/signin')
def auth_signin():
    '''
    Redirect to sina sign in page.
    '''
    ctx.response.set_cookie(COOKIE_REDIRECT, _get_referer())
    client = APIClient(app_key=APP_KEY, app_secret=APP_SECRET, redirect_uri=CALLBACK)
    raise seeother(client.get_authorize_url())

def _get_referer():
    '''
    Get referer url for redirecting after signin.
    '''
    referer = ctx.request.header('REFERER', '/')
    if referer.startswith('http://www.shi-ci.com/'):
        referer = referer[21:]
    if referer.startswith('/auth/'):
        return '/'
    return referer

@get('/auth/callback')
def auth_callback():
    '''
    Callback from sina, then redirect to previous url.
    '''
    code = ctx.request.input(code='').code
    if not code:
        raise seeother('/s/auth_failed')
    client = APIClient(app_key=APP_KEY, app_secret=APP_SECRET, redirect_uri=CALLBACK)
    r = client.request_access_token(code)
    access_token = r.access_token
    expires = r.expires_in
    uid = r.uid
    # get user info:
    client.set_access_token(access_token, expires)
    account = client.users.show.get(uid=uid)
    image = account.get(u'profile_image_url', u'about:blank')
    logging.info('got account: %s' % str(account))
    name = account.get('screen_name', u'') or account.get('name', u'')

    id = u'weibo_%s' % uid
    user = auth.fn_load_user(id)
    if user:
        # update user if necessary:
        db.update('update user set name=?, oauth_image=?, oauth_access_token=?, oauth_expires=? where id=?', \
                name, image, access_token, expires, id)
    else:
        db.insert('user', \
                id = id, \
                name = name, \
                oauth_access_token = access_token, \
                oauth_expires = expires, \
                oauth_url = u'http://weibo.com/u/%s' % uid, \
                oauth_image = image, \
                admin = False)
    # make a signin cookie:
    cookie_str = auth.make_session_cookie(id, access_token, expires)
    logging.info('will set cookie: %s' % cookie_str)
    redirect = ctx.request.cookie(COOKIE_REDIRECT, '/')
    ctx.response.set_cookie(auth.COOKIE_AUTH, cookie_str, expires=expires)
    ctx.response.delete_cookie(COOKIE_REDIRECT)
    raise seeother(redirect)

@get('/auth/signout')
def auth_signout():
    '''
    Sign out and redirect to previous page.
    '''
    ctx.response.delete_cookie(auth.COOKIE_AUTH)
    raise seeother(_get_referer())

########## static page ##########

@get('/weixin')
@template('weixin.html')
def weixin_page():
    return dict(title=u'微信公众号', dynasties=get_dynasties())

@get('/app')
@template('app.html')
def app_page():
    return dict(title=u'中华诗词App', dynasties=get_dynasties())

# search page:
@get('/s')
@template('search.html')
def search():
    i = ctx.request.input(q=u'', dynasty_id='', poet_id='', form='')
    q = i.q
    dynasty_id = ''
    poet_id = ''
    poet = None
    d = dict(title=u'搜索结果', dynasties=get_dynasties(), form=i.form, q=q)
    if 'poet_option' in i:
        d['poet_id'] = i.poet_id
        d['poet_option'] = i.poet_option
        d['poet'] = get_poet(i.poet_option)
        d['search_url'] = '/search?poet_id=%s&form=%s&q=%s' % (i.poet_id, i.form, urllib.quote(q.encode('utf-8')))
    else:
        d['dynasty_id'] = i.dynasty_id
        d['search_url'] = '/search?dynasty_id=%s&form=%s&q=%s' % (i.dynasty_id, i.form, urllib.quote(q.encode('utf-8')))
    return d











@get('/search')
def search_api():
    '''
    Just for search test.
    '''
    i = ctx.request.input(dynasty_id='', poet_id='')
    import httplib
    conn = httplib.HTTPConnection('search.shi-ci.com')
    conn.request('GET', '/search?dynasty_id=%s&poet_id=%s&form=%s&q=%s' % (i.dynasty_id, i.poet_id, i.form, urllib.quote(i.q.encode('utf-8'))))
    resp = conn.getresponse()
    data = resp.read()
    ctx.response.content_type = 'application/json'
    return data
#    return dict(total=100, next='MjQzMzl8My44NDEyODkz', poems=get_featured_poems())




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

def _get_page(str, total_items, pagesize=PAGE_SIZE):
    '''
    Get page object.
    '''
    p = 1
    try:
        p = int(str)
    except ValueError:
        raise web.notfound('invalid page')
    return Page(total_items, p, pagesize)

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

def admin_set_famous(poem_id):
    check_admin()
    web.ctx.db.update('poem', where='id=$id', vars=dict(id=poem_id), ilike=random.randint(100,1000))
    return '200 OK'

def admin_will_add_poem():
    check_admin()
    return _init_dict(title="ADD", locations=(), comments=())

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

def admin_edit_poem(id):
    check_admin()
    L = list(web.ctx.db.select('poem', where='id=$id', vars=dict(id=id)))
    return _init_dict(title="EDIT", locations=(), comments=(), poem=L[0])

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

def _old_auth_failed():
    return _init_dict(title=u'登录失败', locations=((u'中华诗词', '/'), (u'登录失败', None),))

def _old__posted_before(now, dt):
    delta = now - dt
    return delta.days * 86400 + delta.seconds

@api
@get('/m_poem_comments')
def m_poem_comments(id, ps='1'):
    '''
    GET /m_poem_comments/{poem_id}/{page}
    '''
    page = int(ps)
    if page<1 or page>100:
        return r'{"error":"invalid_page","description":"invalid page."}'
    page_size = 20
    offset = page_size * (page - 1)
    L = db.select('select * from poem where id=?', id)
    if not L:
        return r'{"error":"not_found","description":"poem not found."}'
    poem = L[0]
    comments = list(web.ctx.db.select('poem_comment', where='poem_id=$pid', vars=dict(pid=id), offset=offset, limit=page_size+1, order='creation_time desc'))
    has_next = len(comments) > page_size
    if has_next:
        comments = comments[:-1]
    now = datetime.datetime.now()
    return dict(
            page = page, \
            next = has_next, \
            time = time.time(), \
            comments = [dict(user_name=c.user_name, user_image=c.user_image, user_url=c.user_url, content=c.content, posted_before=_posted_before(now, c.creation_time)) for c in comments] \
    )

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

def _old_comment():
    return _comment()

def m_comment():
    return _comment()

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

@api
@get('/m_poem/<id>')
def m_poem(id):
    '''
    GET /m_poem/{poem_id}
    
    Returns:
        Poem json.
    '''
    p = get_poem(id)
    d = dict(**p)
    del d['weibo_id']
    del d['weibo_cht_id']
    return d

@api
@get('/m_categories')
def m_categories():
    return dict(categories=_load_category())

@api
@get('/m_category/<id>')
def m_category(id):
    poems = db.select('select p.* from category_poem cp inner join poem p on cp.poem_id=p.id where cp.category_id=?', id)
    return dict(poems=poems)

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

def share(id):
    '''
    GET /share/{poem_id}
    
    Returns:
        json contains url.
    '''
    return _share(id)

def m_share(id):
    '''
    GET /m_share/{poem_id}

    Returns:
        json contains url.
    '''
    return _share(id)

