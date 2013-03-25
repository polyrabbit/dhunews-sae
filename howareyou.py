#coding=utf-8
import random
import re

import sae.kvdb
import web
import const
from nothing import Nothing
from quotes import quotes

class Howareyou(object):
    def __init__(self):
        ua = web.ctx.environ['HTTP_USER_AGENT']
        ua_mat = re.search('DHU-network-login-helper/(\d+\.\d+)', ua)
        if ua=='XOXOXOXO' or (ua_mat and ua_mat.group(1)<'1.1'):
            # self.update_info = '亲，XX助手已经升级，请至http://dhunews.sinaapp.com/download获取最新版本，如果本程序曾经给您带来不便，我深表歉意-_-。sorry！(如果安装过程中出现“已安装了存在签名冲突的同名数据包”的错误，请先卸载旧版本，再安装最新版本。)'
            self.update_info = '阿勒，你到现在没未升级，不知道因为你的怀旧情怀捏，还是升级时遇到了困难，如果是后者，可以联系我(mcx_221@foxmail.com)帮你解决，希望你能理解。最新版地址http://dhunews.sinaapp.com/download'

    def GET(self):
        kvdb = sae.kvdb.KVClient()
        if hasattr(self, 'update_info'):
            import time
            time.sleep(8)
            raise web.found('/howareyou')
            this_quote = self.update_info
        else:
            try:
                today_quotes = kvdb.get_by_prefix(const.QUOTE_PREFIX)
            except:
                today_quotes = Nothing() #else None is not iterable
            today_quote_probs = 0 if not today_quotes else 3.5
            try:
                weather = kvdb.get('weather')
            except:
                weather = Nothing() #else None is not iterable
            weather_probs = 0 if not weather else 2
            this_quote = Howareyou.weighted_pick([(quotes, 1), ([q[1] for q in today_quotes], today_quote_probs), ([weather], weather_probs)])
        # this_quote = random.choice(quotes)
        # if web.input().get('from') == 'poly':
        # this_quote = '''<p><b>松江天气(<a href='http://www.weather.com.cn/weather/101020900.shtml'>11/21 10:00</a>)</b></p>小雨转小到中雨，东风3-4级，12℃~15℃，当前气温8°。'''
        web.header('Content-Type', 'text/html; charset=utf-8', unique=True)
        web.header('Content-Length', len(this_quote), unique=True)
        web.header('X-How-Are-You', 'fine', unique=True)
        return this_quote
    POST = GET

    @staticmethod
    def weighted_pick(items):
        tot_sum = float(sum(item[1] for item in items))
        probs = [item[1]/tot_sum for item in items]
        r = random.random()
        which = 0
        while r>=0 and which<len(items):
            r -=  probs[which]
            which += 1
        return random.choice(items[which-1][0])

    # import random
    # def random_pick(seq,probabilities):
    #   x = random.uniform(0, 1)
    #     cumulative_probability = 0.0
    #     for item, item_probability in zip(seq, probabilities):
    #         cumulative_probability += item_probability
    #         if x < cumulative_probability: break
    #     return item

    # for i in range(15):
    #     random_pick("abc",[0.1,0.3,0.6])
        
    # 'c'
    # 'b'
    # 'c'
    # 'c'
    # 'a'
    # 'b'
    # 'c'
    # 'c'
    # 'c'
    # 'a'
    # 'b'
    # 'b'
    # 'c'
    # 'a'
    # 'c'
        

class Download(object):
    def GET(self):
        return web.template.frender('templates/download.html')()