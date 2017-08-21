# -*- coding: utf-8 -*-
#__author__="ZJL"

from common.item_manager import Field,DictItem

# 模仿scrapy的Item
class Item(DictItem):
    title = Field()  # 标题
    time = Field()  # 发布时间
    author = Field()  # 作者
    content = Field()  # 文章内容
    images = Field()  # 文章图片
    videos = Field()  # 文章小视频
    discusses = Field()  # 文章评论
    readcount = Field()  # 文章浏览量
    url = Field()  # 文章链接
    jtype = Field()  # 是否解决
    type = Field()  # 类型
    create_time = Field()  # 创建时间
    answers = Field()  # 回答数

