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
import datetime


# codeceo
class Codeceo_Wd_Spider(object):
    name = 'java_codeceo_wd'
    allowed_domains = ["codeceo.com"]
    start_urls = []
    for x in ["java","python"]:#
        for i in range(1,4):
            url = 'http://ask.codeceo.com/tag/'+str(x)+'/page_'+str(i)
            start_urls.append(url)
    yesterday = time.strftime('%Y-%m-%d', time.localtime(time.time() - 60 * 60 * 24))
    mondays = time.strftime('%m-%d', time.localtime(time.time() - 60 * 60 * 24))
    prr = Response()
    headers = random_headers.random_headers()
    rm = UrlManager()

    @asyncErrorLoging(request_error, no_error, "Codeceo_Wd_Spider.getPage")
    @asyncRetry(4, rm.add_error_url)
    async def getPage(self, url):
        async with RequestManager().session as session:
            async with session.get(url, headers=self.headers) as resp:
                print("java_codeceo_wd 1111", resp.status)
                assert resp.status == 200
                # errors="ignore",忽略非法字符
                r_body = await resp.text(errors="ignore")
                rp = Response()
                rp.url = url
                rp.body = r_body
                return rp

    @errorLoging(parse_error, no_error, "Codeceo_Wd_Spider.grabPage")
    def grabPage(self, response):
        response = response.result()
        # print(response.body)
        if response:
            items = response.cssselect(".item")
            for item in items:
                articleTime = item.cssselect("div.item-info > div >span")
                if articleTime:
                    articleTime = articleTime[1].text_content().strip()
                    if "月" in articleTime:
                        num = int(articleTime.replace("个月前提问", ""))
                        now_time = datetime.datetime.now()
                        # 当前时间加半小时
                        yes_time = now_time + datetime.timedelta(days=-30 * num)
                        articleTime = yes_time.strftime('%Y-%m-%d')
                    elif "小时" in articleTime:
                        num = int(articleTime.replace("个小时前提问", ""))
                        articleTime = time.strftime('%Y-%m-%d', time.localtime(time.time() - 60 * 60 * num))
                    elif "天" in articleTime:
                        num = int(articleTime.replace("天前提问", ""))
                        articleTime = time.strftime('%Y-%m-%d', time.localtime(time.time() - 60 * 60 * 24 * num))
                    elif "/" in articleTime:
                        articleTime = articleTime.replace("提问", "").replace("/", "-")
                        if len(articleTime.split("-")[1]) == 1:
                            mon = "0" + articleTime.split("-")[1]
                        else:
                            mon = articleTime.split("-")[1]
                        if len(articleTime.split("-")[2]) == 1:
                            days = "0" + articleTime.split("-")[2]
                        else:
                            days = articleTime.split("-")[2]
                        articleTime = articleTime.split("-")[0] + "-" + mon + "-" + days
                else:
                    articleTime = ""
                # ------------------------------
                # 时间判断
                if self.yesterday != articleTime:
                    continue
                # ==============================
                articleAnswers = item.cssselect(".vbox-number")
                if articleAnswers:
                    articleAnswers = articleAnswers[0].text_content().strip()
                else:
                    articleAnswers = "0"
                articleReadCount = item.cssselect(".vbox-number")
                if articleReadCount:
                    articleReadCount = articleReadCount[0].text_content().strip()
                else:
                    articleReadCount = "0"
                articleAuthor = item.cssselect(".poster-info>span>a")
                if articleAuthor:
                    articleAuthor = articleAuthor[0].text_content().strip()
                else:
                    articleAuthor = ""
                articleTitle = item.cssselect(".item-info>h2>a")
                if articleTitle:
                    articleTitle = articleTitle[0].text_content().strip()
                else:
                    articleTitle = ""
                typex = str(response.url).split("tag/")[1].split("/page")[0]
                Jtype = item.cssselect("div.vbox.answers.answered.solved > small")
                if Jtype:
                    Jtype = Jtype[0].text_content()
                else:
                    Jtype = "未解决"
                self.prr.meta = {
                    "Jtype": Jtype,
                    "typex": typex,
                    "articleTime": articleTime,
                    "articleAuthor": articleAuthor,
                    "articleAnswers": articleAnswers,
                    "articleTitle": articleTitle,
                    "articleReadCount": articleReadCount,
                }
                articleUrl = item.cssselect(".item-info>h2>a")
                if articleUrl:
                    articleUrl = articleUrl[0].get("href")
                    self.prr.url.append(
                        {
                            "url": articleUrl,
                            "upper_url": response.url,
                        }
                    )

    @asyncErrorLoging(request_error, no_error, "Codeceo_Wd_Spider.getPage1")
    @asyncRetry(4, rm.add_error_url)
    async def getPage1(self, url):
        self.headers["Referer"] = url.get("upper_url")
        async with RequestManager().session as session:
            async with session.get(url.get("url"), headers=self.headers) as resp:
                print("java_codeceo_wd 222", resp.status)
                print("java_codeceo_wd 222url", url.get("url"))
                assert resp.status == 200
                # print("222upper_url", url.get("upper_url"))
                # errors="ignore",忽略非法字符
                r_body = await resp.text(errors="ignore")
                rp = Response()
                rp.url = url.get("url")
                rp.body = r_body
                rp.meta = self.prr.meta
                return rp

    @errorLoging(parse_error, no_error, "Codeceo_Wd_Spider.grabPage1")
    def grabPage1(self, response):
        response = response.result()
        if response:
            articleSentence = response.cssselect("div.entry-text.ask-entry")
            if articleSentence:
                articleSentence = response.toString(articleSentence[0]).decode("utf-8")
            else:
                articleSentence = ""
            articleImages_listx = response.cssselect("#AskText > div.entry-text.ask-entry > p > img")
            if articleImages_listx:
                articleImages_list = []
                for articleImages in articleImages_listx:
                    articleImages_list.append(articleImages.get("src"))
            else:
                articleImages_list = []
            articleDiscussesx = response.cssselect("div.content > div.entry-text.answer-entry")
            if articleDiscussesx:
                articleDiscusses = []
                for xx in articleDiscussesx:
                    articleDiscusses.append(xx.text_content().strip())
            else:
                articleDiscusses = []

            articleAnswers = response.meta["articleAnswers"]
            articleTitle = response.meta["articleTitle"]
            articleTime = response.meta["articleTime"]
            articleAuthor = response.meta["articleAuthor"]
            articleReadCount = response.meta["articleReadCount"]
            typex = response.meta["typex"]
            Jtype = response.meta["Jtype"]
            articleUrl = response.url
            articleVideos = []

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
    @errorLoging(main_error, no_error, "Codeceo_Wd_Spider.main")
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

# if __name__ == '__main__':
#     cws = Codeceo_Wd_Spider()
#     cws.main()
