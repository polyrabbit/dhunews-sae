import httplib2
import urllib2
import urllib
import mimetools
import os
from hashlib import md5

import sae.kvdb
import const

def keyWithin200Byte(func):
    def wrapped(*args):
        args = list(args) #tuple to list
        args[1] = httplib2.safename(args[1])
        # if len(args[1])>200:
        #     args = list(args) 
        #     args[1] = md5(args[1]).hexdigest()
        # elif isinstance(args[1], unicode):
        #     args = list(args)
        #     args[1] = args[1].encode('utf-8')
        return func(*args)
    return wrapped

class FileCache(object):
    def __init__(self):
        self.kvdb = sae.kvdb.KVClient()
    
    @keyWithin200Byte
    def get(self, key):
        return self.kvdb.get(key)

    @keyWithin200Byte
    def set(self, key, value):
        self.kvdb.set(key, value, time=86400*30)

    @keyWithin200Byte
    def delete(self, key):
        self.kvdb.delete(key)

    def __del__(self):
        self.kvdb.disconnect_all()

addheaders = [('User-agent', 'Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.4 (KHTML, like Gecko) Chrome/22.0.1229.79 Safari/537.4')]
CACHE = '.cache' if const.isLocal else FileCache()
CACHE = None  # kvdb keeps increasing

def argsDispatcher(func):
    getArgList = lambda cache=CACHE, timeout=const.HTTP_TIMEOUT,\
                 proxy_info=httplib2.ProxyInfo.from_environment,\
                 ca_certs=None, disable_ssl_certificate_validation=False:\
                 (cache, timeout, proxy_info, ca_certs, disable_ssl_certificate_validation)
    def wrapped(self, *args, **kwargs):
        return func(self, *getArgList(*args, **kwargs))
    return wrapped
        

class httplib21(httplib2.Http):
    """enhanced httplib2 with the support of CookieJar"""
    @argsDispatcher
    def __init__(self, *args, **kwargs):
        super(httplib21, self).__init__(*args)
        self.cookieProc = urllib2.HTTPCookieProcessor()
        self.handler = urllib2.HTTPHandler()
        self.addheaders = addheaders
        self.handler.parent = self # for extra headers in urllib2.py line 1125
    
    def request(self, uri, method='GET', **kwargs):
        body = kwargs.get('body', None)
        headers = kwargs.pop('headers', {})
        dummyReq = urllib2.Request(uri, data=body, headers=headers) #procuce a request interface for cookiejar to use
        dummyReq = self.handler.http_request(dummyReq) #for "content-length", "content-type" headers
        self.cookieProc.http_request(dummyReq)

        # self.cookiejar.add_cookie_header(dummyReq)
        cookieHeader = dict(dummyReq.header_items())
        r, c = super(httplib21, self).request(uri, method, headers=cookieHeader or None, **kwargs)
        r.info = lambda :mimetools.Message(self.dict2fp(r))
        r.geturl = lambda :r.get('content-location', uri)
        # self.cookiejar.extract_cookies(r, dummyReq)
        self.cookieProc.http_response(dummyReq, r)
        return r, c

    class dict2fp(object):
        """simulated file object from dict to support readline"""
        def __init__(self, arg):
            self.dict = arg
            self.iter = self.iterdict()
        
        def iterdict(self):
            for k, v in self.dict.iteritems():
                yield '%s: %s' % (k, v)

        def readline(self):
            try:
                return self.iter.next()
            except:
                return '\r\n'

h = httplib21()
def request(url):
    return h.request(url)

if __name__ == '__main__':
	# httplib2.debuglevel = 1

	h = httplib21()
	# h = httplib2.Http('.cache')
	# resp, content = h.request('http://appstack.sinaapp.com/static/doc/release/testing/index.html?a=http://appstack.sinaapp.com/static/doc/release/testing/index.html&a=http://appstack.sinaapp.com/static/doc/release/testing/index.html&a=http://appstack.sinaapp.com/static/doc/release/testing/index.html&a=http://appstack.sinaapp.com/static/doc/release/testing/index.html&a=http://appstack.sinaapp.com/static/doc/release/testing/index.html&a=http://appstack.sinaapp.com/static/doc/release/testing/index.html')
        resp, content = h.request('http://python.sinaapp.com/doc/index.html')
        print 'resp:', resp.geturl()