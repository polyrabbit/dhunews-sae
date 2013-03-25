#coding=utf-8
import web
import urllib2
import urllib
import os
import pprint
import logging
import sys
import re

import sae
import sae.kvdb
import excelParser
import UpdateFeed
import ShiftOldItems
import const
import httplib2
import httplib21
import howareyou
from nothing import Nothing
import notice
import SimpleWordPressRequestHandler
import wipe_outdate_kvdb
import weather

if const.isLocal:
    reload(sys)
    sys.setdefaultencoding('gbk')

url_mapping = (
    '/debug', 'Debug',
    '/download', 'howareyou.Download',
    '/shift_old_items', 'ShiftOldItems.ShiftOldItems',
    '/feed', 'Feed.Feed',
    '/feed_generator', 'UpdateFeed.FeedGen',
    '/howareyou', 'howareyou.Howareyou',
    '/notice', 'notice.Notice',
    '/redirect', 'Redirect',
    '/wipeoutdatekvdb', 'wipe_outdate_kvdb.WipeOutdateKvdb',
    '/robots.txt', 'Robots',
    '/tieba_checkin', 'tieba_checkin.TiebaCheckin',
    '/try', 'Try',
    '/update', 'UpdateFeed.UpdateFeed',
    '/', 'Index',
    '/weather', 'weather.Weather',
    '/xmlrpc.php', 'SimpleWordPressRequestHandler.WPHandler',
    '/(\w+)', 'Index' # must be the last
)
web.config.debug = False
# httplib2.debuglevel = 4
os.environ['disable_fetchurl'] = '1' if const.isLocal else True
# logging.basicConfig(level=logging.DEBUG)

render = web.template.render('templates', base='index', globals=globals())
class Index(object):

    def __init__(self):
        self.db = web.database(dbn='mysql', 
                        host=const.host_s, 
                        db=const.db, 
                        user=const.user, 
                        passwd=const.passwd, 
                        port=const.port
                    )

    def GET(self, channel=const.DEFAULT_CHANNEL):
        ie_mat = re.search('MSIE (\d)\.', web.ctx.environ.get('HTTP_USER_AGENT', str(Nothing())), re.I)
        if ie_mat:
            if 'Opera' not in web.ctx.environ['HTTP_USER_AGENT']\
                    and int(ie_mat.group(1))<7:
                return '<h1>I won\'t render my page in IE %s!!<h1>' % ie_mat.group(1)

        if channel not in const.databases:
            raise web.notfound()

        tot_items = self.db.select(channel, what='count(link) as cnt')[0]['cnt']
        tot_pages = (tot_items+const.ITEMS_PER_PAGE-1)/const.ITEMS_PER_PAGE or 1
        try:
            page = int(web.input().page)
        except:
            page = 1
        if page<1: raise web.found('?page=1')
        if page>tot_pages: raise web.found('?page=%d' % tot_pages)
        # page = max(page, 1)
        # page = min(page, tot_pages)

        offset = const.ITEMS_PER_PAGE*(page-1)
        items = self.db.select(channel, limit=const.ITEMS_PER_PAGE, offset=offset, order='link DESC')
        return render.content(channel, items, page=page, tot_pages=tot_pages)

    POST=GET

class Debug(object):
    def GET(self):
        web.ctx.environ['POST_DATA'] = web.data()
        return pprint.pformat(web.ctx.environ)

    POST=GET
        

class Redirect(object):
    """just send 302 redirections"""
    def GET(self):
        location = web.input(url='/').url
        if not location.startswith(('http://', '/')):
            location = 'http://' + location
        raise web.found(urllib.unquote_plus(location))
    
    POST = GET

class Try(object):
    def GET(self):        
        stor = sae.storage.Client()
        return stor.stat(const.STOR_DOMAIN, "meiriyiwen")
        
class Robots(object):
    def GET(self):
        return 'Sitemap: http://dhunews.sinaapp.com/static/sitemap.xml'
        

# create_tbl_template = '''
# CREATE TABLE IF NOT EXISTS %s (
#   `link` varchar(200) NOT NULL,
#   `title` varchar(200) NOT NULL DEFAULT 'None',
#   `pubDate` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP,
#   `content` text,
#   PRIMARY KEY (`link`)
# ) ENGINE=MyISAM DEFAULT CHARSET=utf8 COMMENT='%s';
# '''

# db = web.database(dbn='mysql', 
#                         host=const.host, 
#                         db=const.db, 
#                         user=const.user, 
#                         passwd=const.passwd, 
#                         port=const.port
#                     )
# for tbln in const.databases.keys():
#     db.query(create_tbl_template % (tbln, tbln))

app = web.application(url_mapping, globals(), web.profiler)
app.notfound = lambda: web.notfound(web.template.frender('templates/404.html')())
application = sae.create_wsgi_app(app.wsgifunc())