#coding=utf-8
from datetime import datetime

import web
import sae.storage
import const
import UpdateFeed

class Feed(object):

    def GET(self):
        channel = web.input(channel='', _unicode=False).channel
        if not channel: raise web.found('/')
        # if 'YoudaoFeedFetcher' in web.ctx.environ['HTTP_USER_AGENT']: raise web.notfound()
        # if 'Superfeedr' in web.ctx.environ['HTTP_USER_AGENT']: raise web.notfound()         
        # if 'Xianguo.com' in web.ctx.environ['HTTP_USER_AGENT']: raise web.notfound()
        # if 'Feedsky' in web.ctx.environ['HTTP_USER_AGENT']: raise web.notfound()
        # if 'Mozilla/4.0 (compatible; Windows;)' == web.ctx.environ['HTTP_USER_AGENT']: raise web.notfound() #QQ      
        # if 'Feedfetcher-Google' not in web.ctx.environ['HTTP_USER_AGENT']: raise web.notfound()
        if channel not in const.databases: raise web.notfound()

        stor = sae.storage.Client()
        if channel not in stor.list(const.STOR_DOMAIN):
            UpdateFeed.FeedGen().POST(channel)

        stat = stor.stat(const.STOR_DOMAIN, channel)
        mtime = stat['datetime']
        etag = stat.get('md5sum', None)
        if web.http.modified(datetime.utcfromtimestamp(mtime), etag):
            web.header('Content-Type', 'application/rss+xml; charset=utf-8')
            return stor.get(const.STOR_DOMAIN, channel).data

    POST = GET
		