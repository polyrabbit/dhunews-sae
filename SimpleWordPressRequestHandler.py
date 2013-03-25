#coding=utf-8
import xmlrpclib
from xmlrpclib import Fault
import sys
import datetime
import time
import re
from functools import partial

import web
import const
import sae.kvdb
from bs4 import BeautifulSoup as BS
from nothing import Nothing

def resolve_dotted_attribute(obj, attr, allow_dotted_names=True):
    """resolve_dotted_attribute(a, 'b.c.d') => a.b.c.d

    Resolves a dotted attribute name to an object.  Raises
    an AttributeError if any attribute in the chain starts with a '_'.

    If the optional allow_dotted_names argument is false, dots are not
    supported and this function operates similar to getattr(obj, attr).
    """

    if allow_dotted_names:
        attrs = attr.split('.')
    else:
        attrs = [attr]

    for i in attrs:
        if i.startswith('_'):
            raise AttributeError(
                'attempt to access private attribute "%s"' % i
                )
        else:
            obj = getattr(obj,i)
    return obj

def list_public_methods(obj):
    """Returns a list of attribute strings, found in the specified
    object, which represent callable attributes"""

    return [member for member in dir(obj)
                if not member.startswith('_') and
                    hasattr(getattr(obj, member), '__call__')]

def remove_duplicates(lst):
    """remove_duplicates([2,2,2,1,3,3]) => [3,1,2]

    Returns a copy of a list without duplicates. Every list
    item must be hashable and the order of the items in the
    resulting list is not defined.
    """
    u = {}
    for x in lst:
        u[x] = 1

    return u.keys()

class SimpleXMLRPCDispatcher:
    """Mix-in class that dispatches XML-RPC requests.

    This class is used to register XML-RPC method handlers
    and then to dispatch them. This class doesn't need to be
    instanced directly when used by SimpleXMLRPCServer but it
    can be instanced when used by the MultiPathXMLRPCServer.
    """

    def __init__(self, allow_none=False, encoding=None):
        self.funcs = {}
        self.instance = None
        self.allow_none = allow_none
        self.encoding = encoding

    def register_instance(self, instance, allow_dotted_names=False):
        """Registers an instance to respond to XML-RPC requests.

        Only one instance can be installed at a time.

        If the registered instance has a _dispatch method then that
        method will be called with the name of the XML-RPC method and
        its parameters as a tuple
        e.g. instance._dispatch('add',(2,3))

        If the registered instance does not have a _dispatch method
        then the instance will be searched to find a matching method
        and, if found, will be called. Methods beginning with an '_'
        are considered private and will not be called by
        SimpleXMLRPCServer.

        If a registered function matches a XML-RPC request, then it
        will be called instead of the registered instance.

        If the optional allow_dotted_names argument is true and the
        instance does not have a _dispatch method, method names
        containing dots are supported and resolved, as long as none of
        the name segments start with an '_'.

            *** SECURITY WARNING: ***

            Enabling the allow_dotted_names options allows intruders
            to access your module's global variables and may allow
            intruders to execute arbitrary code on your machine.  Only
            use this option on a secure, closed network.

        """

        self.instance = instance
        self.allow_dotted_names = allow_dotted_names

    def register_function(self, function, name = None):
        """Registers a function to respond to XML-RPC requests.

        The optional name argument can be used to set a Unicode name
        for the function.
        """

        if name is None:
            name = function.__name__
        self.funcs[name] = function

    def register_introspection_functions(self):
        """Registers the XML-RPC introspection methods in the system
        namespace.

        see http://xmlrpc.usefulinc.com/doc/reserved.html
        """

        self.funcs.update({'system.listMethods' : self.system_listMethods,
                      'system.methodSignature' : self.system_methodSignature,
                      'system.methodHelp' : self.system_methodHelp})

    def register_multicall_functions(self):
        """Registers the XML-RPC multicall method in the system
        namespace.

        see http://www.xmlrpc.com/discuss/msgReader$1208"""

        self.funcs.update({'system.multicall' : self.system_multicall})

    def _marshaled_dispatch(self, data, dispatch_method = None, path = None):
        """Dispatches an XML-RPC method from marshalled (XML) data.

        XML-RPC methods are dispatched from the marshalled (XML) data
        using the _dispatch method and the result is returned as
        marshalled data. For backwards compatibility, a dispatch
        function can be provided as an argument (see comment in
        SimpleXMLRPCRequestHandler.do_POST) but overriding the
        existing method through subclassing is the preferred means
        of changing method dispatch behavior.
        """

        try:
            params, method = xmlrpclib.loads(data)

            # generate response
            if dispatch_method is not None:
                response = dispatch_method(method, params)
            else:
                response = self._dispatch(method, params)
            # wrap response in a singleton tuple
            response = (response,)
            response = xmlrpclib.dumps(response, methodresponse=1,
                                       allow_none=self.allow_none, encoding=self.encoding)
        except Fault, fault:
            response = xmlrpclib.dumps(fault, allow_none=self.allow_none,
                                       encoding=self.encoding)
        except:
            # report exception back to server
            exc_type, exc_value, exc_tb = sys.exc_info()
            response = xmlrpclib.dumps(
                xmlrpclib.Fault(1, "%s:%s" % (exc_type, exc_value)),
                encoding=self.encoding, allow_none=self.allow_none,
                )

        return response

    def system_listMethods(self):
        """system.listMethods() => ['add', 'subtract', 'multiple']

        Returns a list of the methods supported by the server."""

        methods = self.funcs.keys()
        if self.instance is not None:
            # Instance can implement _listMethod to return a list of
            # methods
            if hasattr(self.instance, '_listMethods'):
                methods = remove_duplicates(
                        methods + self.instance._listMethods()
                    )
            # if the instance has a _dispatch method then we
            # don't have enough information to provide a list
            # of methods
            elif not hasattr(self.instance, '_dispatch'):
                methods = remove_duplicates(
                        methods + list_public_methods(self.instance)
                    )
        methods.sort()
        return methods

    def system_methodSignature(self, method_name):
        """system.methodSignature('add') => [double, int, int]

        Returns a list describing the signature of the method. In the
        above example, the add method takes two integers as arguments
        and returns a double result.

        This server does NOT support system.methodSignature."""

        # See http://xmlrpc.usefulinc.com/doc/sysmethodsig.html

        return 'signatures not supported'

    def system_methodHelp(self, method_name):
        """system.methodHelp('add') => "Adds two integers together"

        Returns a string containing documentation for the specified method."""

        method = None
        if method_name in self.funcs:
            method = self.funcs[method_name]
        elif self.instance is not None:
            # Instance can implement _methodHelp to return help for a method
            if hasattr(self.instance, '_methodHelp'):
                return self.instance._methodHelp(method_name)
            # if the instance has a _dispatch method then we
            # don't have enough information to provide help
            elif not hasattr(self.instance, '_dispatch'):
                try:
                    method = resolve_dotted_attribute(
                                self.instance,
                                method_name,
                                self.allow_dotted_names
                                )
                except AttributeError:
                    pass

        # Note that we aren't checking that the method actually
        # be a callable object of some kind
        if method is None:
            return ""
        else:
            import pydoc
            return pydoc.getdoc(method)

    def system_multicall(self, call_list):
        """system.multicall([{'methodName': 'add', 'params': [2, 2]}, ...]) => \
[[4], ...]

        Allows the caller to package multiple XML-RPC calls into a single
        request.

        See http://www.xmlrpc.com/discuss/msgReader$1208
        """

        results = []
        for call in call_list:
            method_name = call['methodName']
            params = call['params']

            try:
                # XXX A marshalling error in any response will fail the entire
                # multicall. If someone cares they should fix this.
                results.append([self._dispatch(method_name, params)])
            except Fault, fault:
                results.append(
                    {'faultCode' : fault.faultCode,
                     'faultString' : fault.faultString}
                    )
            except:
                exc_type, exc_value, exc_tb = sys.exc_info()
                results.append(
                    {'faultCode' : 1,
                     'faultString' : "%s:%s" % (exc_type, exc_value)}
                    )
        return results

    def _dispatch(self, method, params):
        """Dispatches the XML-RPC method.

        XML-RPC calls are forwarded to a registered function that
        matches the called XML-RPC method name. If no such function
        exists then the call is forwarded to the registered instance,
        if available.

        If the registered instance has a _dispatch method then that
        method will be called with the name of the XML-RPC method and
        its parameters as a tuple
        e.g. instance._dispatch('add',(2,3))

        If the registered instance does not have a _dispatch method
        then the instance will be searched to find a matching method
        and, if found, will be called.

        Methods beginning with an '_' are considered private and will
        not be called.
        """

        func = None
        try:
            # check to see if a matching function has been registered
            func = self.funcs[method]
        except KeyError:
            if self.instance is not None:
                # check for a _dispatch method
                if hasattr(self.instance, '_dispatch'):
                    return self.instance._dispatch(method, params)
                else:
                    # call instance method directly
                    try:
                        func = resolve_dotted_attribute(
                            self.instance,
                            method,
                            self.allow_dotted_names
                            )
                    except AttributeError:
                        pass

        if func is not None:
            return func(*params)
        else:
            raise Exception('method "%s" is not supported' % method)

class CGIXMLRPCRequestHandler(SimpleXMLRPCDispatcher):
    """Simple handler for XML-RPC data passed through CGI."""

    def __init__(self, allow_none=False, encoding=None):
        SimpleXMLRPCDispatcher.__init__(self, allow_none, encoding)

    def handle_xmlrpc(self, request_text):
        """Handle a single XML-RPC request"""

        response = self._marshaled_dispatch(request_text)

        web.header('Content-Type', 'text/xml', unique=True)
        web.header('Content-Length', len(response), unique=True)

        return response

class Mt(SimpleXMLRPCDispatcher):
    def __init__(self, store):
        self.store = store

    def _dispatch(self, fn, args):
        self.dispatcher = {'metaWeblog.getRecentPosts': self.getRecentPosts,
                'mt.supportedMethods': self.supportedMethods,
                'metaWeblog.getCategories': self.getCategories,
                'metaWeblog.newPost': self.newPost}

        return self.dispatcher[fn](*args)

    def supportedMethods(self, i=0):
        return sorted(self.dispatcher.keys())

    def getRecentPosts(self, blogid, username, passwd, limit):
        return datetime.datetime.now().strftime('%Y%m%d%H%M')

    def getCategories(self, blogid, username, passwd):
        return {'description':'not found', 'htmlUrl':'http://dhunews.sinaapp.com/howareyou', 'rssUrl':'http://dhunews.sinaapp.com/feed?channel=meiriyiwen'}

    def newPost(self, arg1, username, passwd, post, arg5):
        content = BS(post['description'])
        (content.find('div', class_='crp_related') or Nothing()).decompose()
        [t.unwrap() for t in content.find_all(href=lambda t: t and not t.startswith('http://'))]
        if len(str(content))<2500:
            self.store(str(content))
        return {'url':'http://dhunews.sinaapp.com/howareyou'}

class WPHandler(object):
    def __init__(self):
        try:
            self.kvdb = sae.kvdb.KVClient()
        except:
            self.kvdb = Nothing()

    def POST(self):
        cur_key = const.QUOTE_PREFIX + str(time.time()+86400) #datetime.datetime.today().isoformat()
        handler = CGIXMLRPCRequestHandler()
        handler.register_introspection_functions()
        handler.register_instance(Mt(partial(self.kvdb.set, cur_key))) #timeout won't work
        return handler.handle_xmlrpc(web.data())

    def GET(self):
        if web.input().get('del') and web.input(confirm='')['confirm']=='yes':
            self.kvdb.delete(web.input(_unicode=False).get('del'))
        if not self.kvdb.get_by_prefix(const.QUOTE_PREFIX): return 'not yet.'
        quotes = self.kvdb.get_by_prefix(const.QUOTE_PREFIX)
        body_frag = []
        for q in quotes:
            body_frag.append('<tr><td>%s</td><td>%s</td><td><a href="?del=%s"> X </a></td></tr>' % (q[0], q[1], q[0]))
        body = '<table border="1px">' + ''.join(body_frag) + '</table>'
        web.header('Content-Type', 'text/html; charset=utf-8', unique=True)
        web.header('Content-Length', len(body), unique=True)
        return body

# sae.kvdb.KVClient().delete('quotes_2012-11-20T00:57:01.754429')

# cur_key = 'quotes_1353582306.66'
# sae.kvdb.KVClient().delete(cur_key)

# cur_key = const.QUOTE_PREFIX + '1353581051.907943'
# sae.kvdb.KVClient().set(cur_key, '''<p>当年，弗里德曼的《世界是平的》对我影响最深的一句话：“你可以当会计师，可以当医生，但是不管你当什么，你都要当一个搜索引擎排名靠前者”。</p>''', time=86400)