import web
import urllib
import os
import pprint

import sae

url_mapping = (
    '/?(.*)/', 'Index',
    '/tbl', 'Table',
    '.*/favicon.ico', 'Favicon'
    )

class Index:
    """docstring for index"""
    def GET(self, path):
        i = web.input(name='')        
        #pprint.pprint(web.ctx.Storage)
        return pprint.PrettyPrinter().pformat(web.ctx)
        return "hellp"+path+'\n'+i.name

class Table:
    """docstring for Table"""
    def GET(self):
        app_root = os.path.dirname(__file__)
        templates_root = os.path.join(app_root, 'templates')
        render = web.template.render(app_root)
        #print app_root
        return render.tbl()
        

class Favicon:
    """docstring for Favicon"""
    def GET(self):
        return urllib.urlopen('http://www.google.com/favicon.ico').read()

app = web.application(url_mapping, globals())
if __name__ == '__main__' and 'SERVER_SOFTWARE' not in os.environ:
    app.run()

application = sae.create_wsgi_app(app.wsgifunc())