#coding: utf-8
import time
import datetime
import re
import const
import sae.kvdb

class WipeOutdateKvdb(object):
    def GET(self):
        kvdb = sae.kvdb.KVClient()
        expired = []

        if kvdb.get_by_prefix(const.QUOTE_PREFIX):
	        items = kvdb.get_by_prefix(const.QUOTE_PREFIX)
	        expired = filter(lambda item: float(item[0].rpartition('_')[-1])<=time.time(), items)
        if kvdb.get('weather'):
        	today = datetime.date.today().strftime('%m/%d')
        	try:
	        	update_day = re.search(r'>(\d{1,2}/\d{1,2})', kvdb.get('weather')).group(1)
	        except:
	        	update_day = '12/31'
	        if update_day<today:
	        	expired.append(('weather', None))
        map(lambda item: kvdb.delete(item[0]), expired)
        return expired