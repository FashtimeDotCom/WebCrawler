# -*- coding: utf-8 -*-
#__author__="ZJL"

from pymongo import MongoClient


# 伪模仿scrapy的Pipeline
# 这是Mongodb的写入
class MongoPipeline(object):
    def __init__(self):
        host = "127.0.0.1"
        port = 27017
        dbName = "py_demo"
        self.client = MongoClient(host=host, port=port)
        self.db = self.client[dbName]

    def process_item(self, item, spider_name):
        try:
            post = self.db[spider_name]
            post.insert(dict(item))
            return item
        except Exception as e:
            return e
        finally:
            self.client.close()