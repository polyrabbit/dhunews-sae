#coding=utf-8
import os
import sys
import re
import nothing
from urlparse import urljoin
import httplib21
import urllib2
import itertools
from bs4 import BeautifulSoup as BS, Tag, NavigableString

candidate_tags = frozenset(['a', 'caption', 'dl', 'dt', 'dd', 'div', 'ol', 'li', 'ul', 'p', 'pre', 'table', 'tbody', 'thead', 'tfoot', 'tr', 'td', 'br', 'h1', 'h2', 'article'])
ignore_tags = frozenset(['option', 'script', 'noscript', 'style', 'iframe'])
minor_patt = re.compile(r'comment|combx|disqus|foot|header|menu|rss|shoutbox|sidebar|sponsor|vote', re.IGNORECASE)
major_patt = re.compile(r'article|entry|post|body|column|main|content|section', re.IGNORECASE)
maxScore = 0
maxItemList = []

# todo 根据是否_blank加分

def isCandidateTag(node):
    return node.name in candidate_tags
def isIgnoreTag(node):
    return node.name in ignore_tags
def isMajorTag(node):
    return major_patt.search(node.get('id', '')+''.join(node.get('class', [])))
def isMinorTag(node):
    return minor_patt.search(node.get('id', '')+''.join(node.get('class', [])))
def containsALink(node):
    return not isinstance(node, NavigableString) and (node.name=='a' or node.a)

def PageListParser(url):
    resp, cont = httplib21.request(url)
    if resp.fromcache: return nothing.Nothing()
    if resp.info().getmaintype() != 'text':
        raise NotImplementedError('we expect a text format, not the %s' % resp.info().gettype())
    charset = resp.info().getparam('charset') # or None
    docRoot = BS(cont, from_encoding=charset)
    return digest(parse(docRoot)[1], resp.geturl())

def parse(curNode, depth=0.1):
    breaksHere = lambda node: not (isinstance(node, NavigableString) or (node.name==curTagName and node.get('class')==curTagClass))
    score = 0
    itemList = []
    if not curNode.visited==True and isCandidateTag(curNode): # not curNode.visited==True, the ==True cannot be omitted
        curTagName = curNode.name
        curTagClass = curNode.get('class')
        consistency = 0
        totLen = 0
        for node in itertools.chain([curNode], curNode.next_siblings):
            if breaksHere(node): break
            if not containsALink(node): continue # bug here what if the first tag doesnot contain A link
            #NavigableString has been filtered above
            longestA = getLongestA(node)
            if longestA.get('href', '#').startswith(('#', 'mailto')): continue            
            consistency += 1
            totLen += getTextLen(node) + getExtraLen(node)
            node.visited = True
            itemList.append(node)
        score = totLen*consistency**1.2*depth
        # global maxScore, maxItemList
        # if score > maxScore:
        #     maxScore, maxItemList = score, itemList

    return max((score, itemList), max(([0, []]+[parse(childNode, depth+0.1) for childNode in curNode.children if isinstance(childNode, Tag)])))
    # for childNode in curNode.children:
    #     if isinstance(childNode, Tag):
    #         parse(childNode, depth+0.1)


# curNode cannot be a string
def getTextLen(curNode):
    if getattr(curNode, 'textLen', None) is not None:
        return curNode.textLen
    textLen = 0
    for node in curNode.children:
        if isinstance(node, Tag) and not isIgnoreTag(node):
            textLen += getTextLen(node)
        elif type(node) is NavigableString: # not isinstance(node, NavigableString) in case of Comment
            textLen += len(node.string.strip())
    curNode.textLen = textLen
    return textLen

def digest(itemList, baseUrl):
    entries = []
    for item in itemList:
        aLink = getLongestA(item)
        link = urljoin(baseUrl, aLink.get('href'))
        title = aLink.get_text().strip()
        entries.append({'link': link, 'title': title})
    # entries.sort(reverse=True)
    return sorted(entries, key=lambda e: e['link'], reverse=True)

def getLongestA(node):
    if getattr(node, 'longestA') is not None:
        return node.longestA

    # the caller should guarantee there exists an A-link
    alinks = []
    if node.name=='a':
        alinks.append(node)
    alinks.extend(node.find_all('a'))
    # in case of <a class="voice_title" href="#"><a href="/voice/show/?vid=82">tttt</a></a>
    node.longestA = max(alinks, key=lambda n: (getTextLen(n), -len(list(n.descendants))))
    return node.longestA

def getExtraLen(node):
    extraLen = 0
    if isMajorTag(node):
        extraLen = getTextLen(getLongestA(node))
    if isMinorTag(node):
        extraLen -= getTextLen(getLongestA(node))*0.8
    return extraLen

if __name__ == '__main__':
    pageUrl = 'http://voice.meiriyiwen.com/voice/past'
    pageUrl = 'http://jw.dhu.edu.cn/dhu/news/newslist.jsp'
    pageUrl = 'http://youth.dhu.edu.cn/channel.asp?id=13'
    # pageUrl = 'http://www2.dhu.edu.cn/dhuxxxt/xinwenwang/xyjz.asp'
    # pageUrl = 'http://www2.dhu.edu.cn/dhuxxxt/xinwenwang/zdhd.asp'
    pageUrl = 'http://www.infzm.com/author/%E5%88%98%E6%9C%AA%E9%B9%8F/'
    # pageUrl = 'http://www.killman.net/forum-18-1.html'
    pageUrl = 'http://222.204.208.4/pub/model/twogradepage/newsmore.aspx?colname=%E5%85%AC%E5%91%8A'
    page = PageListParser(pageUrl)
    for i in page:
        print i['link'], i['title'].encode('utf-8')
    # print len(page)