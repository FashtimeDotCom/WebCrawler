# -*- coding: utf-8 -*-
#__author__="ZJL"

# 日志管理器
# 错误分两个等级，只有尾号1会触发邮件提醒，日志文件过大也会触发邮件
# 使用尾号区分是为了用前面的数字可以记录抓取阶段表示
import logging
import os
import traceback
import time
from common.email_manager import batchSendEmail
from setting import logfilename, errortitle


yesterday = time.strftime('%Y-%m-%d', time.localtime(time.time()))

def objLogging(errorcode, errortext):
    logging.basicConfig(level=logging.DEBUG,
                        format='%(asctime)s %(filename)s[line:%(lineno)d] %(levelname)s %(message)s',
                        datefmt='%a, %d %b %Y %H:%M:%S',
                        filename=yesterday+logfilename,
                        filemode='a+')

    console = logging.StreamHandler()
    console.setLevel(logging.INFO)
    formatter = logging.Formatter('%(name)-12s: %(levelname)-8s %(message)s')
    console.setFormatter(formatter)
    logging.getLogger('').addHandler(console)

    if errorcode[-1] == "0":
        text = errortext + "\n" + traceback.format_exc()
        logging.debug(text)
    elif errorcode[-1] == "1":
        text = errortext + "\n" + traceback.format_exc()
        logging.warning(text)
        try:
            # 发送邮件，也可以用另一种实现方式将错误码和错误信息以键值对的形式存在redis中，再写一个服务每天读取一天数据如果有尾号是1的错误就发送邮件通知
            batchSendEmail(errortitle, text)
        except Exception as e:
            # print(traceback.format_exc())
            logging.warning(traceback.format_exc())
    else:
        text = errortext + "\n" + traceback.format_exc()
        logging.warning(text)

    # 如果日志文件过大就发邮件通知删除，不过我这里以日期为日志名应该不会用到所以注释掉
    # filesize = os.path.getsize(yesterday+logfilename)
    # if filesize >= 3000000:
    #     try:
    #         batchSendEmail("日志文件过大", "日志文件大小大于3M，请及时处理")
    #     except Exception as e:
    #         # print(traceback.format_exc())
    #         logging.warning(traceback.format_exc())


# 用于有协程的日志修饰器
def asyncErrorLoging(errorcode, errornocode,errortext):
    def wrapper(func):
        async def wrapper(*args, **kwargs):
            try:
                return await func(*args, **kwargs)
            except Exception as e:
                objLogging(errorcode,errortext)
            finally:
                objLogging(errornocode, errortext)
        return wrapper
    return wrapper


# 用于普通的日志修饰器
def errorLoging(errorcode, errornocode,errortext):
    def wrapper(func):
        def wrapper(*args, **kwargs):
            try:
                return func(*args, **kwargs)
            except Exception as e:
                objLogging(errorcode,errortext)
            finally:
                objLogging(errornocode, errortext)
        return wrapper
    return wrapper