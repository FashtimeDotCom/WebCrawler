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

# csdn
class Csdn_Spider(object):
    name = 'java_csdn'
    start_urls = []
    for x in ["java","python"]:#"python"
        for i in range(1,5):#1383
            url = 'http://ask.csdn.net/'+str(x)+'/p'+str(i)
            start_urls.append(url)
    yesterday = time.strftime('%Y-%m-%d', time.localtime(time.time() - 60 * 60 * 24))
    prr = Response()
    headers = random_headers.random_headers()
    rm = UrlManager()

    @asyncErrorLoging(request_error, no_error, "Csdn_Spider.getPage")
    @asyncRetry(4, rm.add_error_url)
    async def getPage(self, url):
        async with RequestManager().session as session:
            async with session.get(url, headers=self.headers) as resp:
                print("java_csdn 1111", resp.status)
                assert resp.status == 200
                # errors="ignore",忽略非法字符
                r_body = await resp.text(errors="ignore")
                rp = Response()
                rp.url = url
                rp.body = r_body
                return rp

    @errorLoging(parse_error, no_error, "Csdn_Spider.grabPage")
    def grabPage(self, response):
        response = response.result()
        # print(response.body)
        if response:
            detail_cons = response.cssselect(".questions_detail_con")
            bar_cons = response.cssselect(".share_bar_con")
            if detail_cons and bar_cons:
                for detail_con,bar_con in zip(detail_cons,bar_cons):
                    articleReadCount = bar_con.cssselect("em[class*=browse]")
                    if articleReadCount:
                        articleReadCount = articleReadCount[0].text_content().split("浏览")[1]
                    else:
                        articleReadCount = ""

                    articleTime = detail_con.cssselect(".q_time>span")
                    if articleTime:
                        articleTime = articleTime[0].text_content().split(" ")[0].replace(".", "-")
                    else:
                        articleTime = ""
                    # -----------------------------
                    # 时间判断
                    if articleTime != self.yesterday:
                        continue
                    # =============================
                    articleAuthor = detail_con.cssselect("a[class*=user_name]")
                    if articleAuthor:
                        articleAuthor = articleAuthor[0].text_content()
                    else:
                        articleAuthor = ""
                    articleTitle = detail_con.cssselect("a[href*=questions]")
                    if articleTitle:
                        articleTitle = articleTitle[0].text_content()
                    else:
                        articleTitle = ""
                    Jtype = detail_con.cssselect("a[class*=answer_num]")
                    if Jtype:
                        Jtype = Jtype[0].get("title")
                    else:
                        Jtype = ""
                    articleAnswers = detail_con.cssselect("a[class*=answer_num]>span")
                    if articleAnswers:
                        articleAnswers = articleAnswers[0].text_content()
                    else:
                        articleAnswers = "0"
                    self.prr.meta = {
                        "type": str(response.url).split("net/")[1].split("/p")[0],
                        "articleTime": articleTime,
                        "articleAuthor": articleAuthor,
                        "articleTitle": articleTitle,
                        "Jtype": Jtype,
                        "articleAnswers": articleAnswers,
                        "articleReadCount": articleReadCount,
                    }
                    articleUrl = detail_con.cssselect("a[href*=questions]")
                    if articleUrl:
                        articleUrl = articleUrl[0].get("href")
                        self.prr.url.append(
                            {
                                "url": articleUrl,
                                "upper_url": response.url,
                            }
                        )

    @asyncErrorLoging(request_error, no_error, "Csdn_Spider.getPage1")
    @asyncRetry(4, rm.add_error_url)
    async def getPage1(self, url):
        self.headers["Referer"] = url.get("upper_url")
        async with RequestManager().session as session:
            async with session.get(url.get("url"), headers=self.headers) as resp:
                print("java_csdn 222", resp.status)
                # print("222url", url.get("url"))
                assert resp.status == 200
                # print("222upper_url", url.get("upper_url"))
                # errors="ignore",忽略非法字符
                r_body = await resp.text(errors="ignore")
                rp = Response()
                rp.url = url.get("url")
                rp.body = r_body
                rp.meta = self.prr.meta
                return rp

    @errorLoging(parse_error, no_error, "Csdn_Spider.grabPage1")
    def grabPage1(self, response):
        response = response.result()
        if response:
            articleSentence = response.cssselect(".questions_detail_con")
            if articleSentence:
                articleSentence = response.toString(articleSentence[0]).decode("utf-8")
            else:
                articleSentence = ""
            articleDiscussesx = response.cssselect(".answer_detail_con>div>p")
            if articleDiscussesx:
                articleDiscusses = []
                for xx in articleDiscussesx:
                    articleDiscusses.append(xx.text_content())
            else:
                articleDiscusses = []
            articleImages_listx = response.cssselect("img[alt*=图片说明]")
            if articleImages_listx:
                articleImages_list = []
                for xx in articleImages_listx:
                    articleImages_list.append(xx.get("src"))
            else:
                articleImages_list = []
            articleVideos = []
            articleTime = response.meta["articleTime"]
            articleAuthor = response.meta["articleAuthor"]
            articleTitle = response.meta["articleTitle"]
            Jtype = response.meta["Jtype"]
            type = response.meta["type"]
            articleAnswers = response.meta["articleAnswers"]
            articleReadCount = response.meta["articleReadCount"]
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
            item["type"] = type
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
#     cs = Csdn_Spider()
#     cs.main()
