#coding=utf-8
import os
import sys
import re
import httplib21
from urlparse import urljoin
import urllib2
import cStringIO
from PIL import Image
from bs4 import BeautifulSoup as BS, Tag, NavigableString
import httplib21
from excelParser import excelParser
from nothing import Nothing

#beautifulsoup will convert all tag names to lower-case
candidate_tags = frozenset(['a', 'caption', 'dl', 'dt', 'dd', 'div', 'ol', 'li', 'ul', 'p', 'pre', 'table', 'tbody', 'thead', 'tfoot', 'tr', 'td', 'br', 'h1', 'h2'])
ignore_tags = frozenset(['option', 'script', 'noscript', 'style', 'iframe'])
minor_patt = re.compile(r'comment|combx|disqus|foot|header|menu|rss|shoutbox|sidebar|sponsor|vote', re.IGNORECASE)
major_patt = re.compile(r'article|entry|post|column|main|content|section|title|text', re.IGNORECASE)

def isCandidateTag(node): #is_candidate_tag
    return node.name in candidate_tags
def isIgnoreTag(node): #is_ignore_tag
    return node.name in ignore_tags
def isMajorTag(node): #is_major_tag
    return major_patt.search(node.get('id', '')+''.join(node.get('class', [])))
def isMinorTag(node): #is_minor_tag
    return node.name=='a' or minor_patt.search(node.get('id', '')+''.join(node.get('class', [])))

def cutOff(nodes):
    return filter(lambda n:isinstance(n, Tag) and not isIgnoreTag(n), nodes)

class imgArea(object):
    def __init__(self, bs_node):
        self.bs_node = bs_node      
        self.scale = 22*22
        self.img_area_px = self.calcArea()

    def calcArea(self):
        minpix = 55 # mind the side-bar pics
        height = self.bs_node.get('height', Nothing()).strip().rstrip('px')
        width = self.bs_node.get('width', Nothing()).strip().rstrip('px')

        # if you use percentage in height or width,
        # in most cases it cannot be the main-content
        if height.endswith('%') or width.endswith('%'):
            return 0
        try: height = int(height)
        except: height = 0
        try: width = int(width)
        except: width = 0

        if 0<height<=minpix or 0<width<=minpix:
            return 0

        if not (height and width):
            fp = cStringIO.StringIO()
            try:
                r, c = httplib21.request(self.bs_node['src'])
                fp.write(c)
                fp.seek(0)
                w, h = Image.open(fp).size
            except:
                h = w = 1.0
            finally:
                hdw = h/float(w) # we need float here
                if not (height or width):
                    height, width = h, w # no need to convert
                elif not height:
                    height = int(hdw*width)
                else:
                    width = int(hdw*height)
                fp.close()

        if height<=minpix or width<=minpix:
            return 0
        return width*height

    def toTextLen(self):
        return self.img_area_px/self.scale
 
        

class ArticleExtractor(object):
    def __init__(self, headers, cont):
        self.max_score = 0
        self.article = Nothing() # if there being no tags, it can return nothing.
        charset = headers.info().getparam('charset') # or None
        # what's the more elegent way?
        dom_tree = BS(cont.replace('<br>', '<br />'), from_encoding=charset)

        self.title = dom_tree.title
        self.base_url = headers.geturl()
        self.extract(dom_tree)

        # clean ups
        self.cleanUpHtml()
        self.relativePath2AbsUrl()

    def extract(self, cur_node, depth=0.1):
        if isCandidateTag(cur_node):
            text_len = self.textLen(cur_node)
            img_len = self.imgAreaLen(cur_node)
            bonus = self.extraScore(cur_node, 'majorLen')
            penalty = self.extraScore(cur_node, 'minorLen')
            score = (text_len+img_len-penalty*0.8+bonus)*(depth**1.5) # yes 1.5 is a big number
            # cur_node.score = score

            if score > self.max_score:
                self.max_score, self.article = score, cur_node

        for child in cur_node.children: # the direct children, not descendants
            if isinstance(child, Tag):
                self.extract(child, depth+0.1)

    def extraScore(self, cur_node, len_type='majorLen'):
        if isinstance(cur_node, NavigableString):
            return 0
        if getattr(cur_node, len_type, None) is not None:
            return getattr(cur_node, len_type)
        checkTag = isMajorTag if len_type=='majorLen' else isMinorTag
        if checkTag(cur_node):
            setattr(cur_node, len_type, self.textLen(cur_node)+self.imgAreaLen(cur_node))
            return getattr(cur_node, len_type)

        extra_len = 0
        for node in cutOff(cur_node.children):
            if checkTag(node):
                setattr(node, len_type, self.textLen(node)+self.imgAreaLen(cur_node))
            else:
                self.extraScore(node, len_type)
            extra_len += getattr(node, len_type)
        setattr(cur_node, len_type, extra_len)
        return extra_len

    def textLen(self, cur_node):
        if getattr(cur_node, 'text_len', None) is not None:
            return cur_node.text_len
        text_len = 0
        for node in cur_node.children:
            if isinstance(node, Tag) and not isIgnoreTag(node):
                text_len += self.textLen(node)
            elif type(node) is NavigableString: # not isinstance(node, NavigableString) in case of Comment
                text_len += len(node.string.strip())
        cur_node.text_len = text_len
        return text_len

    def imgAreaLen(self, cur_node):
        if getattr(cur_node, 'img_len', None) is not None:
            return cur_node.img_len
        img_len = 0
        if cur_node.name=='img':
            img_len = imgArea(cur_node).toTextLen()
        else:
            for node in cutOff(cur_node.children):
                img_len += self.imgAreaLen(node)
        cur_node.img_len = img_len
        return img_len

    def cleanUpHtml(self):
        trashcan = []
        for tag in self.article.descendants:
            if isinstance(tag, Tag):
                del tag['class']
                del tag['id']
                if tag.name in ignore_tags:
                    trashcan.append(tag)
            elif isinstance(tag, NavigableString) and type(tag) is not NavigableString:
                # tag.extract()
                trashcan.append(tag)

        # map(lambda t: getattr(t, 'decompose', t.extract)(), trashcan)
        [getattr(t, 'decompose', t.extract)() for t in trashcan if t.__dict__]

    def relativePath2AbsUrl(self):
        def _rp2au(soup, tp):
            d = {tp: True}
            for tag in  soup.find_all(**d):
                tag[tp] = urljoin(self.base_url, tag[tp])
        _rp2au(self.article, 'href')
        _rp2au(self.article, 'src')
        _rp2au(self.article, 'background')

    def getMainContent(self):
        return self.getArticle()

    def getArticle(self):
        return self.article

    def geturl(self):
        return self.base_url

    def getTitle(self):
        return self.title.string

    def getTitlePrefix(self):
        return ''


# dispatcher
def PageContentParser(url):
        resp, cont = httplib21.request(url)
        if resp.info().getmaintype() == 'text':
            return ArticleExtractor(resp, cont)
        elif resp.info().gettype() == 'application/vnd.ms-excel':
            return excelParser(cont)
        elif resp.info().gettype() == 'application/msword':
            getMainContent = lambda self : u'再等等，或许下辈子我会看懂<a target="_blank" href="http://download.microsoft.com/download/0/B/E/0BE8BDD7-E5E8-422A-ABFD-4342ED7AD886/Word97-2007BinaryFileFormat%28doc%29Specification.pdf">word的格式</a>。'
            getTitlePrefix = lambda self : u'[DOC]'
            return type('MsWord', (), {'getMainContent':getMainContent, 'getTitlePrefix':getTitlePrefix})()
        else:
            raise TypeError('I have no idea how the %s is formatted' % resp.info().gettype())

if __name__ == '__main__':
    import httplib2
    # httplib2.debuglevel = 4
    pageUrl = 'http://www.infzm.com/content/81698'
    pageUrl = 'http://meiriyiwen.com/'
    pageUrl = 'http://cmse.dhu.edu.cn/contentViewCtrl.do?contentID=5b64ce823b7f7060013b87bcdc590005'
    pageUrl = 'http://222.204.208.4/pub/model/twogradepage/newsdetail.aspx?id=588&columnId=33'
    # pageUrl = 'http://youth.dhu.edu.cn/content.asp?id=1947'
    # pageUrl = 'http://www2.dhu.edu.cn/dhuxxxt/xinwenwang/shownews.asp?id=18824'
    # pageUrl = 'http://youth.dhu.edu.cn/content.asp?id=1951'
    # pageUrl = 'http://youth.dhu.edu.cn/content.asp?id=1993'
    # pageUrl = 'http://www2.dhu.edu.cn/dhuxxxt/xinwenwang/shownews.asp?id=18750'
    # pageUrl = 'http://www2.dhu.edu.cn/dhuxxxt/xinwenwang/shownews.asp?id=18826'
    page = PageContentParser(pageUrl)
    c =page.getMainContent()
    print (c.encode('utf-8'))