# -*- coding: utf-8 -*-
#__author__="ZJL"


import threading
import time
from spiders.java_51cto import Cto_Spider
from spiders.java_codeceo import Codeceo_Spider
from spiders.java_codeceo_wd import Codeceo_Wd_Spider
from spiders.java_csdn import Csdn_Spider

start = time.time()

# 将爬虫项目添加进列表中
spider_list = [
    Cto_Spider(),
    Codeceo_Spider(),
    Codeceo_Wd_Spider(),
    Csdn_Spider(),


]

threads = []

for spider in spider_list:
    t = threading.Thread(target=spider.main())
    threads.append(t)

for t in threads:
    t.setDaemon(True)
    t.start()

print("%s Elapsed Time: %s" % ("run.main",time.time() - start))
