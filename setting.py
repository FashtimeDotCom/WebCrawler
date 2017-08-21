# -*- coding: utf-8 -*-
#__author__="ZJL"

# 接收邮箱
toEmail = ["xxxxxxxx@qq.com"]

smtp_connect = "smtp.163.com"

# 发送邮箱
emailName = "xxxxxx@163.com"

# 邮箱密码
emailPassword = "xxxxx"

# redisIP
redis_host = "127.0.0.1"

# redis端口
redis_port = 6379

# redisDB
redis_db = 0

# 日志文件名
logfilename = "Logging.log"

# 邮件标题
errortitle = "程序错误报告"


# 请求头部信息
headers = [
            {
                "Upgrade-Insecure-Requests": "1",
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.36",
                "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
                "Accept-Encoding": "gzip, deflate, sdch, br",
                "Accept-Language": "zh-CN,zh;q=0.8",
                },
           ]