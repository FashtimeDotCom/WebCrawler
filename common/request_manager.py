# -*- coding: utf-8 -*-
#__author__="ZJL"

import aiohttp
import lxml.html


# 请求管理器
class RequestManager(object):
    def __init__(self):
        self.session = aiohttp.ClientSession()

    def get(self, url, *, allow_redirects=True, **kwargs):
        return self.session.get(url, allow_redirects=True, **kwargs)

    def post(self, url, *, data=None, **kwargs):
        return self.session.post(url, data=None, **kwargs)


# Response对象和CSS选择器
class Response(object):
    def __init__(self):
        self.body = ""
        self.url = []
        self.upper_url = ""
        self.meta = {}
    # css选择器
    def cssselect(self,strc):
        xhtml = lxml.html.fromstring(self.body)
        return xhtml.cssselect(strc)
    # xpath选择器
    def xpath(self,strc):
        xhtml = lxml.html.document_fromstring(self.body)
        return xhtml.xpath(strc)
    # 对象string
    def toString(self,strc,encoding='utf-8'):
        xhtml = lxml.html.tostring(strc,pretty_print=True, encoding=encoding)
        return xhtml
