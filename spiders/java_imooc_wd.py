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


# imooc_wd
class ImoocWd_Spider(object):
    name = 'java_imooc_wd'
    allowed_domains = ["imooc.com"]
    type_dict = {
        "3":"java",
    }
    # "18": "python",
    # "22": "AngularJS",
    start_urls = []
    for x in type_dict:
        for i in range(1,2):
            url = 'http://www.imooc.com/wenda/'+str(x)+'/recommend/'+str(i)
            start_urls.append(url)
    yesterday = time.strftime('%Y-%m-%d', time.localtime(time.time() - 60 * 60 * 24))
    prr = Response()
    headers = random_headers.random_headers()
    rm = UrlManager()

    @asyncErrorLoging(request_error, no_error, "ImoocWd_Spider.getPage")
    @asyncRetry(4, rm.add_error_url)
    async def getPage(self, url, callback=None):
        async with RequestManager().session as session:
            async with session.get(url, headers=self.headers) as resp:
                print("1111", resp.status)
                assert resp.status == 200
                # errors="ignore",忽略非法字符
                r_body = await resp.text(errors="ignore")
                rp = Response()
                rp.url = url
                rp.body = r_body
                callback(rp)

    @errorLoging(parse_error, no_error, "ImoocWd_Spider.grabPage")
    def grabPage(self, response):
        # print(response.body)
        if response.body:
            ques_answers = response.cssselect(".ques-answer")
            if ques_answers:
                for ques_answer in ques_answers:
                    # --------------------------------------------
                    # 没回答的踢掉
                    Pdyx = ques_answer.cssselect("span.signature")
                    if not Pdyx:
                        continue
                    # ============================================
                    typex = str(response.url).split("wenda/")[1].split("/recommend")[0]
                    if typex:
                        typex = self.type_dict.get(typex, "")
                    else:
                        typex = ""
                    articleTitle = ques_answer.cssselect("div.ques-con > a")
                    if articleTitle:
                        articleTitle = articleTitle[0].text_content().strip()
                    else:
                        articleTitle = ""
                    Jtype = ques_answer.cssselect("span.had-solve")
                    if Jtype:
                        Jtype = Jtype[0].text_content()
                    else:
                        Jtype = "未解决"
                    self.prr.meta = {
                        "Jtype": Jtype,
                        "articleTitle": articleTitle,
                        "typex": typex,
                    }
                    articleUrl = ques_answer.cssselect("div.ques-con > a")
                    if articleUrl:
                        articleUrl = "http://www.imooc.com" + articleUrl[0].get("href")
                        self.prr.url.append(
                            {
                                "url": articleUrl,
                                "upper_url": response.url,
                            }
                        )

    @asyncErrorLoging(request_error, no_error, "ImoocWd_Spider.getPage1")
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

    @errorLoging(parse_error, no_error, "ImoocWd_Spider.grabPage1")
    def grabPage1(self, response):
        if response.body:
            articleTime = response.cssselect("span.time")
            if articleTime:
                articleTime = articleTime[0].text_content().strip()
                if "小时前" in articleTime:
                    num = int(articleTime.replace("小时前", ""))
                    articleTime = time.strftime('%Y-%m-%d', time.localtime(time.time() - 60 * 60 * num))
                elif "天前" in articleTime:
                    num = int(articleTime.replace("天前", ""))
                    articleTime = time.strftime('%Y-%m-%d', time.localtime(time.time() - 60 * 60 * 24 * num))
                else:
                    articleTime = articleTime
            else:
                articleTime = ""
            # -------------------------------------
            # 时间判断
            if self.yesterday == articleTime:
            # ======================================
                articleSentence = response.cssselect("#js-content-main")
                if articleSentence:
                    articleSentence = response.toString(articleSentence[0]).decode("utf-8")
                else:
                    articleSentence = ""
                articleImages_listx = response.cssselect("#js-qa-wenda > p > img")
                if articleImages_listx:
                    articleImages_list = []
                    for xx in articleImages_listx:
                        articleImages_list.append(xx.get("src"))
                else:
                    articleImages_list = []
                articleAuthor = response.cssselect("#js-content-main > div.detail-q-title.clearfix > div > div.detail-user.l > a.author.l > img")
                if articleAuthor:
                    articleAuthor = articleAuthor[0].get("alt")
                else:
                    articleAuthor = ""
                print(articleAuthor)
                articleAnswers = response.cssselect(".ans_num")
                if articleAnswers:
                    articleAnswers = articleAnswers[0].text_content().strip().replace("回答", "")
                else:
                    articleAnswers = "0"
                articleDiscussesx = response.cssselect("div.answer-content.rich-text.aimgPreview")
                if articleDiscussesx:
                    articleDiscusses = []
                    for xx in articleDiscussesx:
                        articleDiscusses.append(xx.text_content().strip())
                else:
                    articleDiscusses = []

                articleReadCount = "0"
                articleVideos = []
                articleTitle = response.meta["articleTitle"]
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


    @errorLoging(main_error, no_error, "ImoocWd_Spider.main")
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
#     iws = ImoocWd_Spider()
#     iws.main()