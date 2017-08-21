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


# iteye
class Iteye_Spider(object):
    name = 'java_iteye'
    start_urls = []
    for x in ["java"]:
        for i in range(1,2):#299
            url = 'http://www.iteye.com/problems/search?page=' + str(i) + '&query=' + str(x)
            start_urls.append(url)
    yesterday = time.strftime('%Y-%m-%d', time.localtime(time.time() - 60 * 60 * 24))
    mondays = time.strftime('%m-%d', time.localtime(time.time() - 60 * 60 * 24))
    prr = Response()
    headers = random_headers.random_headers()
    rm = UrlManager()

    @asyncErrorLoging(request_error, no_error, "Iteye_Spider.getPage")
    @asyncRetry(4, rm.add_error_url)
    async def getPage(self, url, callback=None):
        async with RequestManager().session as session:
            async with session.get(url, headers=self.headers) as resp:
                print("1111", resp.status)
                # read()是获取二进制响应内容
                assert resp.status == 200
                # errors="ignore",忽略非法字符
                r_body = await resp.text(errors="ignore")
                rp = Response()
                rp.url = url
                rp.body = r_body
                callback(rp)

    @errorLoging(parse_error, no_error, "Iteye_Spider.grabPage")
    def grabPage(self, response):
        # print(response.body)
        if response.body:
            question_summarys = response.cssselect(".question-summary")
            if question_summarys:
                for question_summary in question_summarys:
                    articleTime = question_summary.cssselect("span[class*=gray]")
                    if articleTime:
                        articleTime = articleTime[0].text_content().split(" ")[0].replace("年","-").replace("月","-").replace("日","")
                    else:
                        articleTime = ""
                    # --------------------------------
                    # 时间判断
                    # if self.yesterday != articleTime:
                    #     continue
                    # ===================================
                    articleTitle = question_summary.cssselect(".summary>h3>a")
                    if articleTitle:
                        articleTitle = articleTitle[0].text_content().strip()
                    else:
                        articleTitle = ""
                    Jtype = question_summary.cssselect(".summary>h3>.status")
                    if Jtype:
                        Jtype = Jtype[0].text_content().strip()
                    else:
                        Jtype = ""
                    articleAnswers = question_summary.cssselect(".ask_number")
                    if articleAnswers:
                        articleAnswers = articleAnswers[0].text_content().strip()
                    else:
                        articleAnswers = "0"
                    articleReadCount = question_summary.cssselect(".statscontainer>div[class*=gray]")
                    if articleReadCount:
                        articleReadCount = articleReadCount[0].text_content().strip().split(" ")[0]
                    else:
                        articleReadCount = "0"
                    articleAuthor = question_summary.cssselect(".user_blog>a")
                    if articleAuthor:
                        articleAuthor = articleAuthor[0].text_content().strip()
                    else:
                        articleAuthor = ""
                    typex = str(response.url).split("query=")[1]
                    self.prr.meta = {
                        # 时间
                        "articleTime": articleTime,
                        # 标题
                        "articleTitle": articleTitle,
                        # 是否解决
                        "Jtype": Jtype,
                        # 回答数
                        "articleAnswers": articleAnswers,
                        # 阅读数
                        "articleReadCount": articleReadCount,
                        # 作者
                        "articleAuthor": articleAuthor,
                        # 类型
                        "typex": typex,
                    }
                    articleUrl = question_summary.cssselect(".summary>h3>a")
                    if articleUrl:
                        articleUrl = "http://www.iteye.com" + articleUrl[0].get("href")
                        self.prr.url.append(
                            {
                                "url": articleUrl,
                                "upper_url": response.url,
                            }
                        )

    @asyncErrorLoging(request_error, no_error, "Iteye_Spider.getPage1")
    @asyncRetry(4, rm.add_error_url)
    async def getPage1(self, url, callback=None):
        self.headers["Referer"] = url.get("upper_url")
        async with RequestManager().session as session:
            async with session.get(url.get("url"), headers=self.headers) as resp:
                print("222", resp.status)
                # print("222url", url.get("url"))
                assert resp.status == 200
                # print("222upper_url", url.get("upper_url"))
                # errors="ignore",忽略非法字符
                r_body = await resp.text(errors="ignore")
                rp = Response()
                rp.url = url.get("url")
                rp.body = r_body
                rp.meta = self.prr.meta
                callback(rp)

    @errorLoging(parse_error, no_error, "Iteye_Spider.grabPage1")
    def grabPage1(self, response):
        if response.body:
            articleSentence = response.cssselect(".new_content")
            if articleSentence:
                articleSentence = response.toString(articleSentence[0]).decode("utf-8")
            else:
                articleSentence = ""
            articleDiscussesx = response.cssselect(".sproblem_right>P")
            if articleDiscussesx:
                articleDiscusses = []
                for xx in articleDiscussesx:
                    articleDiscusses.append(xx.text_content())
            else:
                articleDiscusses = []

            articleImages_list = []
            articleVideos = []
            articleAnswers = response.meta["articleAnswers"]
            articleTitle = response.meta["articleTitle"]
            articleTime = response.meta["articleTime"]
            articleAuthor = response.meta["articleAuthor"]
            articleReadCount = response.meta["articleReadCount"]
            typex = response.meta["typex"]
            Jtype = response.meta["Jtype"]
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


    @errorLoging(main_error, no_error, "Iteye_Spider.main")
    def main(self):
        start = time.time()

        loop = asyncio.get_event_loop()

        tasks = [self.getPage(url, self.grabPage) for url in self.start_urls]
        loop.run_until_complete(asyncio.gather(*tasks))

        print("ddddddddddd")

        tasks1 = [self.getPage1(url, self.grabPage1) for url in self.prr.url]
        loop.run_until_complete(asyncio.gather(*tasks1))

        print("%s Elapsed Time: %s" % (self.name, time.time() - start))

        loop.close()

# if __name__ == '__main__':
#     ies = Iteye_Spider()
#     ies.main()