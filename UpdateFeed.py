#coding=utf-8
import logging
import os
import sys
from datetime import date, datetime
import json
import re
import cPickle as pickle
from urllib import quote_plus
import traceback

import web
from sae.taskqueue import Task, TaskQueue, add_task
import sae.storage
from PageContentParser import PageContentParser
from PageListParser import PageListParser
import const
import feedgenerator

# MEIRIYIWEN_URL = 'http://meiriyiwen.com/?date='
DATE_FORMAT = '%Y-%m-%d'
violationAcc = logging.getLogger('violation_access')
violationAcc.setLevel(logging.WARNING)

injectionlog = logging.getLogger('injection_on_dbname')
injectionlog.setLevel(logging.WARNING)

sh = logging.StreamHandler()
fmt = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
sh.setFormatter(fmt)

violationAcc.addHandler(sh)
injectionlog.addHandler(sh)

date_patt = re.compile(r'(?P<year>\d{4})?\D(?P<month>\d{1,2})\D(?P<day>\d{1,2})(\D(?P<hour>\d{1,2}))?(\D(?P<minute>\d{1,2}))?(\D(?P<second>\d{1,2}))?', re.U)

def webauth(action):
    def wrappedAction(self):
        if 'SAE' not in web.ctx.environ['HTTP_USER_AGENT'].upper() and not const.isLocal:
            violationAcc = logging.getLogger('violation_access')
            violationAcc.warning(web.ctx.environ)
            raise web.seeother('/')
        return action(self)
    return wrappedAction

def dateSniffer(text):
    date_mat = date_patt.search(unicode(text)) # text now is Tag type
    dt = {}
    if date_mat:
        if date_mat.group('year'): dt['year'] = int(date_mat.group('year'))
        if date_mat.group('month'): dt['month'] = int(date_mat.group('month'))
        if date_mat.group('day'): dt['day'] = int(date_mat.group('day'))
        if date_mat.group('hour'): dt['hour'] = int(date_mat.group('hour'))
        if date_mat.group('minute'): dt['minute'] = int(date_mat.group('minute'))
        if date_mat.group('second'): dt['second'] = int(date_mat.group('second'))
        try:
            return datetime.today().replace(**dt)
        except:
            return None
    return None


class UpdateFeed(object):

    # @webauth
    def __init__(self):
        self.db = web.database(dbn='mysql', 
                            host=const.host, 
                            db=const.db, 
                            user=const.user, 
                            passwd=const.passwd, 
                            port=const.port
                        )

    def GET(self):
        channels = web.input(channel=[], _unicode=False).channel
        queue = TaskQueue('web_content_fetcher')
        ret = []

        for channel in channels:
            newslist = []
            # channel = channel.encode('ascii')
            if channel not in const.databases:
                injectionlog = logging.getLogger('injection_on_dbname')
                injectionlog.warning(channel+' - '+str(web.ctx.environ))
                continue

            if channel=='meiriyiwen':
                link = const.databases[channel]+date.today().strftime(DATE_FORMAT)
                if not self.contains(channel, link):
                    newslist.append({'link': link, 'pubDate': None, 'tbln': channel})

            else:
                url = const.databases[channel]
                #on windows mysql stores tables on filesystem, hence the table name is case-insensitive,
                #but on *nix they are case-sensitive
                # channel = channel.lower()
                pages = PageListParser(url)
                for p in pages:
                    #p is sorted in desc, so if we find one then the rest is ignored
                    if self.contains(channel, p['link']): break
                    dt = dateSniffer(p['title'])
                    if dt:                        
                        p['pubDate'] = dt
                    p['tbln'] = channel
                    newslist.append(p)

            if newslist:
                queue.add((Task('/update', pickle.dumps(news)) for news in newslist))
                queue.add(Task('/feed_generator', channel))
                ret.append('DONE IN DISPATCHING %s' % channel)
        return '\n'.join(ret) if ret else "IT'S UP-TO-DATE"

    def contains(self, tbln, link):
        return bool(self.db.select(tbln, where='link=$link', vars=locals(), limit=1))

    def POST(self): 
        news = pickle.loads(web.data()) #TODO: too dangerous here
        try:
            if 'content' not in news:
                page = PageContentParser(news['link'])
                news['content'] = page.getMainContent()
            # if hasattr(page, 'getTitle'):
            if not news.get('title', None):
                news['title'] = page.getTitle()
            news['title'] = getattr(page, 'getTitlePrefix', lambda: '')() + news['title']
            if 'pubDate' not in news:
                content = getattr(news['content'], 'get_text', lambda : news['content'])()
                news['pubDate'] = dateSniffer(content) or datetime.today()

            # on Jan 29, 2013 to add school-notices in howareyou
            notice = {'title': news['title'], 'date': news['pubDate'], 'link': news['link'], 'dept': news['tbln']}
            add_task('web_content_fetcher', '/notice', str(notice))

            self.db.insert(news.pop('tbln'), **news)
        except Exception, e:
            if const.isLocal:
                traceback.print_exc()
                os._exit(1)
            raise
        return 'DONE IN FETCHING %s' % news['link']


class FeedGen(object):

    # @webauth
    #it will be called from /feed
    def __init__(self):
        self.db = web.database(dbn='mysql', 
                        host=const.host_s, 
                        db=const.db, 
                        user=const.user, 
                        passwd=const.passwd, 
                        port=const.port
                    )

    def POST(self, tbln=None):
        tbln = tbln or web.data()
        if tbln not in const.databases:
            raise web.webapi.Forbidden('<h1>403 Forbidden</h1>')
        # comment = self.db.query('SHOW TABLE STATUS where name=$tbln', locals())[0].Comment
        comment = const.comments[tbln]

        feed = feedgenerator.DefaultFeed(
            title = comment,
            link = u"http://dhunews.sinaapp.com",
            feed_url = u"http://dhunews.sinaapp.com/feed",
            author_name = 'polyrabbit',
            author_email = 'http://polyrabbit.github.com/contact_me.html',
            ttl = '240',
            description = comment,
            language = u"zh-CN"
        )

        items = self.db.select(tbln, limit=const.MAX_RSS_ITEMS, order='link DESC')
        for item in items:
            feed.add_item(
                title = item['title'],
                link = item['link'],
                unique_id = item['link'],
                pubdate = item['pubDate'],
                # summary
                categories = (comment, ),
                description = item['content']
            )

        ob = sae.storage.Object(feed.writeString('utf-8'), content_type='application/rss+xml')
        stor = sae.storage.Client()
        stor.put(const.STOR_DOMAIN, tbln, ob)
        return 'DONE IN STORAGE'

    if const.isLocal:
        GET = lambda self: self.POST(web.input(channel='ph', _unicode=False).channel)
    else:
        def GET(self):
            raise web.webapi.Forbidden('<h1>403 Forbidden</h1>')
    # GET = lambda self: self.POST(web.input(channel='ph', _unicode=False).channel) #本地环境与线上不匹配呀


def test_dateSniffer(text):
    print dateSniffer(text)

def test():
    test_dateSniffer("""周鸿颖、钟平老师课程教室调整的通知
 
松江校区周鸿颖老师《大学物理1》教室更改为1101（周一3-4节）、1137（周四5-6节）。《光电子学》教室更改为1137（周四7-8节）。
 
松江校区钟平老师《大学物理1》教室更改为2137（周一5-6节）、1121（周四1-2节）。
 
请同学们相互转告！
 
                               教务处
                            2013.3.4""".decode('utf-8'))

if __name__ == '__main__':
    test()