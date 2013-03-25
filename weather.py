#coding: utf-8
import datetime
import time
import urllib2
import const
import json

import sae.kvdb

url_cityinfo = 'http://m.weather.com.cn/data/101020900.html'
url_weatherinfo = 'http://www.weather.com.cn/data/sk/101020900.html'

class Weather(object):
    def GET(self):
        for i in range(10):
            weatherinfo = json.loads(urllib2.urlopen(url_weatherinfo).read())['weatherinfo']
            p_hour = time.strptime(weatherinfo['time'], '%H:%M').tm_hour
            if p_hour==time.localtime().tm_hour: break
            time.sleep(1)
        else:
            return 'Not modified'
        weatherinfo.update(json.loads(urllib2.urlopen(url_cityinfo).read())['weatherinfo'])
        weather_desc = u'''<p><b>松江天气(<a href='http://www.weather.com.cn/weather/101020900.shtml'>{date} {time}</a>)</b></p>{weather}，{wind}，{temp_range}，当前气温{temp_now}°。'''.format(
            date = datetime.date.today().strftime('%m/%d'),
            time = weatherinfo['time'],
            weather = weatherinfo['weather1'],
            temp_range = weatherinfo['temp1'],
            wind = weatherinfo['wind1'],
            temp_now = weatherinfo['temp'])
        sae.kvdb.KVClient().set('weather', weather_desc.encode('utf-8'))
        return weather_desc.encode('utf-8')