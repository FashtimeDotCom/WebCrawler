# -*- coding: utf-8 -*-
#__author__="ZJL"


import asyncio
import time
from common import random_headers
from common.request_manager import RequestManager,Response
from items import Item
from pipelines import MongoPipeline
from common.request_common import asyncRetry
from common.url_manager import UrlManager
from common.log_manager import asyncErrorLoging,errorLoging
from common.error_code import parse_error,insert_error,no_error,main_error,request_error


class Cto_Spider(object):
    # 数据库表名
    name = 'java_cto'
    # 起始url列表
    start_urls = []
    for x in ["java",]:#"python"
        for i in range(1, 2):  # 6725
            url = 'http://so.51cto.com/index.php?project=blog&keywords=' + str(x) + '&sort=time&p=' + str(i)
            start_urls.append(url)
    # 当前日期前一天
    yesterday = time.strftime('%Y-%m-%d', time.localtime(time.time() - 60 * 60 * 24))
    # Response对象
    prr = Response()
    # 随机header(在这里申明说明这个类的所有请求都用这个头信息，如果要每次改变请求头信息将这个申明放在请求函数中)
    headers = random_headers.random_headers()
    # URL的redis对象
    rm = UrlManager()

    # 记入日志,第三个参数记录类名和函数名便于在日志中定位错误
    @asyncErrorLoging(request_error,no_error,"Cto_Spider.getPage")
    # 重试机制，错误url存进redis
    @asyncRetry(4,rm.add_error_url)
    async def getPage(self,url,callback=None):
        async with RequestManager().session as session:
            async with session.get(url,headers=self.headers) as resp:
                # print("1111",resp.status)
                # 断言，报错会进入重试机制
                assert resp.status == 200
                r_body = await resp.text(errors="ignore")
                # Response对象
                rp = Response()
                rp.url = url
                rp.body = r_body
                # 将Response对象传给函数
                callback(rp)

    # 记入日志,第三个参数记录类名和函数名便于在日志中定位错误
    @errorLoging(parse_error,no_error,"Cto_Spider.grabPage")
    # 页面解析
    def grabPage(self,response):
        # print(response.body)
        if response.body:
            # html = lxml.html.fromstring(response.body)
            # td = html.cssselect(".res-doc")
            td = response.cssselect(".res-doc")
            if len(td):
                for t in td:
                    articleTimes = t.cssselect("ul>li")
                    if len(articleTimes):
                        articleTime = articleTimes[1].text_content().split(" ")[1].strip()
                        articleUrl = articleTimes[0].text_content()
                    else:
                        articleTime = ""
                        articleUrl = ""
                    # -----------------------------------
                    # 时间判断
                    if articleTime != self.yesterday:
                        continue
                    # ===================================
                    # print("aaa222",articleTime)
                    # print("aaaa222",articleUrl)
                    self.prr.url.append(
                        {
                            "url":articleUrl,
                            "upper_url":response.url,
                        }
                    )
                    self.prr.meta = {
                        "articleTime": articleTime,
                        # "articleTitle":articleTitle,
                        "type": response.url.split("keywords=")[1].split("&")[0],
                    }


    # 记入日志,第三个参数记录类名和函数名便于在日志中定位错误
    @asyncErrorLoging(request_error,no_error,"Cto_Spider.getPage1")
    # 进入详细页面
    @asyncRetry(4,rm.add_error_url)
    async def getPage1(self,url,callback=None):
        self.headers["Referer"] = url.get("upper_url")
        async with RequestManager().session as session:
            async with session.get(url.get("url"),headers=self.headers) as resp:
                print("222",resp.status)
                print("222url",url.get("url"))
                assert resp.status == 200
                # print("222upper_url", url.get("upper_url"))
                r_body = await resp.text(errors="ignore")
                rp = Response()
                rp.url = url.get("url")
                rp.body = r_body
                rp.meta = self.prr.meta
                callback(rp)

    # 记入日志,第三个参数记录类名和函数名便于在日志中定位错误
    @errorLoging(parse_error,no_error,"Cto_Spider.grabPage1")
    # 详细页面解析,入库
    def grabPage1(self, response):
        if response.body:
            articleTitle = response.cssselect("title")
            if articleTitle:
                articleTitle = articleTitle[0].text_content().strip()
            else:
                articleTitle = ""
            articleSentence = response.cssselect(".showContent")
            if articleSentence:
                # print(type(articleSentence[0]))
                # print(type(response.toString(articleSentence[0])))
                articleSentence = response.toString(articleSentence[0]).decode("utf-8")
            else:
                articleSentence = ""
            articleImages_listx = response.cssselect("div.showContent > p > a > img")
            if articleImages_listx:
                articleImages_list = []
                for x in articleImages_listx:
                    articleImages_list.append(x.get("src"))
            else:
                articleImages_list = []
            articleReadCount = response.cssselect("#readNum")
            if articleReadCount:
                articleReadCount = articleReadCount[0].text_content().strip()
            else:
                articleReadCount = "0"
            articleDiscussesx = response.cssselect(".commentcontent")
            if articleDiscussesx:
                articleDiscusses = []
                for x in articleDiscussesx:
                    articleDiscusses.append(x.text_content().strip())
            else:
                articleDiscusses = []
            articleAuthor = response.cssselect("body > div.blogMain > div.blogLeft > div.box.moduleUser > div.title > h2 > a > strong")
            if articleAuthor:
                articleAuthor = articleAuthor[0].text_content().strip()
            else:
                articleAuthor = ""
            articleVideos = []
            Jtype = ""
            articleAnswers = "0"
            articleTime = response.meta["articleTime"]
            typex = response.meta["type"]
            articleUrl = response.url

            print("ccvd",articleUrl)

            item = Item()
            # 回答数
            item["answers"] = articleAnswers
            # 标题
            item["title"] = articleTitle
            # 时间
            item["time"] = articleTime
            # 作者
            item["author"] = articleAuthor
            # 内容
            item["content"] = articleSentence
            # 链接
            item["url"] = articleUrl
            # 图片链接
            item["images"] = articleImages_list
            # 视频链接
            item["videos"] = articleVideos
            # 回答
            item["discusses"] = articleDiscusses
            # 类型
            item["type"] = typex
            # 是否解决
            item["jtype"] = Jtype
            # 阅读数
            item["readcount"] = articleReadCount
            # 创建时间
            item["create_time"] = time.strftime('%Y-%m-%d', time.localtime(time.time()))
            # 入库
            MongoPipeline().process_item(item,self.name)


    # 记入日志,第三个参数记录类名和函数名便于在日志中定位错误
    @errorLoging(main_error, no_error, "Cto_Spider.main")
    # 主函数
    def main(self):
        start = time.time()
        # 创建时间循环
        loop = asyncio.get_event_loop()

        # 创建任务
        tasks = [self.getPage(url,self.grabPage) for url in self.start_urls]
        # 将任务放进事件循环中
        loop.run_until_complete(asyncio.gather(*tasks))

        print("dddddddddddddddd")

        # 将同一层级的请求加入一个任务中
        tasks1 = [self.getPage1(url,self.grabPage1)for url in self.prr.url]
        loop.run_until_complete(asyncio.gather(*tasks1))

        print("%s Elapsed Time: %s" % (self.name, time.time() - start))

        # 关闭时间循环
        loop.close()



# 单个爬虫测试(单个爬虫调试时用)
if __name__ == '__main__':
    cs = Cto_Spider()
    cs.main()