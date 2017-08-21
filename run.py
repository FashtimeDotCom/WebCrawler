# -*- coding: utf-8 -*-
#__author__="ZJL"


import threading
import time
from spiders.java_51cto import Cto_Spider

start = time.time()

# 将爬虫项目添加进列表中
spider_list = [Cto_Spider().main(),]

# 有几个爬虫就开几个线程
for i in spider_list:
    t =threading.Thread(target=i)
    t.start()

print("%s Elapsed Time: %s" % ("run.main",time.time() - start))