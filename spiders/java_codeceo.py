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
from common.error_code import parse_error,no_error,main_error,request_error


class Codeceo_Spider(object):
    name = 'java_codeceo'
    start_urls = []
    for x in ["java","python" ]:  #"python"
        for i in range(1, 5):  # 38
            url = 'http://www.codeceo.com/article/tag/' + str(x) + '/page/' + str(i)
            start_urls.append(url)
    yesterday = time.strftime('%Y-%m-%d', time.localtime(time.time() - 60 * 60 * 24))
    mondays = time.strftime('%m-%d', time.localtime(time.time() - 60 * 60 * 24))
    prr = Response()
    headers = random_headers.random_headers()
    rm = UrlManager()

    @asyncErrorLoging(request_error, no_error, "Codeceo_Spider.getPage")
    @asyncRetry(4, rm.add_error_url)
    async def getPage(self, url):
        async with RequestManager().session as session:
            async with session.get(url, headers=self.headers) as resp:
                print("java_codeceo 1111",resp.status)
                assert resp.status == 200
                r_body = await resp.text(errors="ignore")
                rp = Response()
                rp.url = url
                rp.body = r_body
                return rp

    @errorLoging(parse_error,no_error,"Codeceo_Spider.grabPage")
    def grabPage(self,response):
        response = response.result()
        # print(response.body)
        if response:
            # html = lxml.html.fromstring(response.body)
            # td = html.cssselect(".res-doc")
            excerpts = response.cssselect(".excerpt")
            if excerpts:
                for excerpt in excerpts:
                    articleTime = excerpt.cssselect(".time")
                    if articleTime:
                        articleTime = articleTime[0].text_content()
                    else:
                        articleTime = ""
                    # ===============================
                    # 时间判断
                    if self.mondays != articleTime:
                        continue
                    # ----------------------------------
                    articleAnswers = excerpt.cssselect(".comm")
                    if articleAnswers:
                        articleAnswers = articleAnswers[0].text_content().split("人")[0]
                    else:
                        articleAnswers = "0"

                    articleTitle = excerpt.cssselect("h3>a")
                    if articleTitle:
                        articleTitle = articleTitle[0].text_content()
                    else:
                        articleTitle = ""
                    typex = str(response.url).split("tag/")[1].split("/page")[0]
                    self.prr.meta = {
                        "typex": typex,
                        "articleTime": articleTime,
                        "articleAnswers": articleAnswers,
                        "articleTitle": articleTitle,
                    }
                    articleUrl = excerpt.cssselect("h3>a")
                    if articleUrl:
                        articleUrl = articleUrl[0].get("href")
                        self.prr.url.append(
                            {
                                "url": articleUrl,
                                "upper_url": response.url,
                            }
                        )

    @asyncErrorLoging(request_error, no_error, "Codeceo_Spider.getPage1")
    # 进入详细页面
    @asyncRetry(4, rm.add_error_url)
    async def getPage1(self, url):
        self.headers["Referer"] = url.get("upper_url")
        async with RequestManager().session as session:
            async with session.get(url.get("url"), headers=self.headers) as resp:
                print("java_codeceo 222", resp.status)
                print("java_codeceo 222url", url.get("url"))
                assert resp.status == 200
                # print("222upper_url", url.get("upper_url"))
                r_body = await resp.text(errors="ignore")
                rp = Response()
                rp.url = url.get("url")
                rp.body = r_body
                rp.meta = self.prr.meta
                return rp

    @errorLoging(parse_error, no_error, "Codeceo_Spider.grabPage1")
    def grabPage1(self, response):
        response = response.result()
        if response:
            articleAuthor = response.cssselect("a[ref=nofollow]")
            if articleAuthor:
                articleAuthor = articleAuthor[0].text_content()
            else:
                articleAuthor = ""
            articleSentence = response.cssselect(".article-entry")
            if articleSentence:
                articleSentence = response.toString(articleSentence[0]).decode("utf-8")
            else:
                articleSentence = ""
            articleImages_listx = response.cssselect("img[src*=images]")
            if articleImages_listx:
                articleImages_list = []
                for articleImages in articleImages_listx:
                    articleImages_list.append(articleImages.get("src"))
            else:
                articleImages_list = []
            articleVideos = []
            articleDiscusses = []
            Jtype = ""
            articleReadCount = "0"
            articleAnswers = response.meta["articleAnswers"]
            typex = response.meta["typex"]
            articleTime = response.meta["articleTime"]
            articleTitle = response.meta["articleTitle"]
            articleUrl = response.url

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
            MongoPipeline().process_item(item, self.name)

    # 记入日志,第三个参数记录类名和函数名便于在日志中定位错误
    @errorLoging(main_error, no_error, "Codeceo_Spider.main")
    # 主函数
    def main(self):
        start = time.time()

        # 创建时间循环
        loop = asyncio.get_event_loop()

        for url in self.start_urls:
            coroutine = self.getPage(url)
            # 添加任务
            task = asyncio.ensure_future(coroutine)
            # 回调
            task.add_done_callback(self.grabPage)
            # 事件循环
            loop.run_until_complete(task)

        print("ddddddddddd")

        for url in self.prr.url:
            coroutine = self.getPage1(url)
            # 添加任务
            task = asyncio.ensure_future(coroutine)
            # 回调
            task.add_done_callback(self.grabPage1)
            # 事件循环
            loop.run_until_complete(task)

        print("%s Elapsed Time: %s" % (self.name, time.time() - start))

# # 单个爬虫测试(单个爬虫调试时用)
# if __name__ == '__main__':
#     cs = Codeceo_Spider()
#     cs.main()
