#coding=utf-8
import datetime
import time
import urllib
import ast
import sae.kvdb
import const
import web

dept_name = {
    'dhu_jw': u'教务网',
    'dhu_news_zdhd': u'东华新闻网',
    'dhu_youth': u'东华共青团',
    'dhu_xyjz': u'校园讲座',
    'dhu_gs': u'研究生部',
}

class Notice(object):
    def GET(self):
        raise web.notfound()

    def POST(self):
        # notice = ast.literal_eval(web.data()) #TODO: too dangerous(evil info to deliver)
        # notice['date'] is a datetime type, literal_eval won't accept that.
        notice = eval(web.data()) #TODO: too dangerous(evil info to deliver)
        if notice.get('dept') not in dept_name:
            return 'you are not welcome here, %s.' % notice.get('notice')
        try:
            kvdb = sae.kvdb.KVClient()
        except:
            return 'KVDB is ill. - by notice.py'

        longest_duration = datetime.datetime.today()+datetime.timedelta(days=3)
        expire_time = notice['date'] or longest_duration
        if not datetime.datetime.today()<expire_time<=longest_duration:
            expire_time = longest_duration

        key = const.QUOTE_PREFIX + str(time.mktime(expire_time.timetuple()))
        # 'a %s' % u'c' turns out to be unicode, while 'a{0}'.format(u'c') a str-type 
        body = u"""<a href='{link}'>{title}</a> --<font color='#aabb00'>{dept}</font>""".format(
            link = const.REDIRECT_PREFIX + urllib.quote_plus(notice['link']), # for statistics
            title = notice['title'],
            dept = dept_name[notice['dept']],
            ).encode('utf-8')
        kvdb.set(key, body)
        return 'Done in %s' % notice['title']