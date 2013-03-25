import const
import web
import logging

import MySQLdb

class ShiftOldItems(object):
    def __init__(self):
        self.conn = MySQLdb.connect(host=const.host,
                                    user=const.user,
                                    passwd=const.passwd,
                                    db=const.db,
                                    port=const.port,
                                    charset='utf8')

    def GET(self):
        if 'sae' not in web.ctx.environ['HTTP_USER_AGENT'].lower() and not const.isLocal:
            violationAcc = logging.getLogger('violation_access')
            violationAcc.warning(web.ctx)
            raise web.seeother('/')

        channels = web.input(channel=[]).channel
        cursor = self.conn.cursor()
        for channel in channels:
            if channel not in const.databases:
                injectonlog = logging.getLogger('injection_on_dbname')
                injectonlog.warning(channel+' - '+str(web.ctx))
                continue
            try:
                cursor.execute('set @row_cnt = (select link from %s order by link desc limit %s, 1);delete from %s where link<=@row_cnt' % (channel, const.max_row_cnt, channel))
            except:
                pass
        cursor.close()
        return 'DONE'

    def __del__(self):
        self.conn.commit()
        self.conn.close()

    POST = GET