#coding=utf-8
import os
import collections
import sae.const

isLocal = 'SERVER_SOFTWARE' not in os.environ

host = (sae.const.MYSQL_HOST, '127.0.0.1')[isLocal]
host_s = (sae.const.MYSQL_HOST_S, '127.0.0.1')[isLocal]
user = (sae.const.MYSQL_USER, 'root')[isLocal]
passwd = (sae.const.MYSQL_PASS, 'admin')[isLocal]
db = (sae.const.MYSQL_DB, 'app_dhunews')[isLocal]
port = (int(sae.const.MYSQL_PORT), 3306)[isLocal]

max_row_cnt = 400
HTTP_TIMEOUT = 24
MAX_RSS_ITEMS = 15
ITEMS_PER_PAGE = 8

# databases = set(['meiriyiwen', '77pZx', 'wvIxQ', 'FsoiM']) #谷歌的服务在国内真是不稳定呀
databases = {
    'dhu_jw': 'http://jw.dhu.edu.cn/dhu/index.jsp',
    'dhu_news_zdhd': 'http://www2.dhu.edu.cn/dhuxxxt/xinwenwang/zdhd.asp',
    'dhu_youth': 'http://youth.dhu.edu.cn/channel.asp?id=13',
    'dhu_xyjz': 'http://www2.dhu.edu.cn/dhuxxxt/xinwenwang/xyjz.asp',
    'infzm_lwp': 'http://www.infzm.com/author/%E5%88%98%E6%9C%AA%E9%B9%8F/',
    'meiriyiwen': 'http://meiriyiwen.com/?date=',
    'dhu_gs': 'http://yjsdep.dhu.edu.cn/',
    'dhu_cmse_lab_announcement': 'http://222.204.208.4/pub/model/twogradepage/newsmore.aspx?colname=%E5%85%AC%E5%91%8A',
}
comments = collections.OrderedDict([
    ('dhu_jw', u'东华大学教务网'),
    ('dhu_news_zdhd', u'东华新闻网-重大活动'),
    ('dhu_youth', u'东华大学共青团'),
    ('dhu_xyjz', u'东华大学校园讲座'),
    ('meiriyiwen', u'每日一文'),
    ('infzm_lwp', u'南方周末 - 刘未鹏'),
    ('dhu_gs', u'东华大学研究生部'),
    ('dhu_cmse_lab_announcement', u'材料学院实验室'),
])

HOST = ['http://dhunews.sinaapp.com/', 'http://localhost:8080/'][isLocal]
REDIRECT_PREFIX = HOST+'redirect?url='

QUOTE_PREFIX = 'quotes_'
# NOTICE_PREFIX = 'notice_'

STOR_DOMAIN = 'feed'
DEFAULT_CHANNEL = 'meiriyiwen'

GMT_FORMAT = '%a, %d %b %Y %H:%M:%S GMT'