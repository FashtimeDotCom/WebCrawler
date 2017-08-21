# -*- coding: utf-8 -*-
#__author__="ZJL"

import random
import setting

# 随机返回headers
def random_headers():
    head_len = len(setting.headers)
    num = random.randint(0,head_len-1)
    return setting.headers[num]