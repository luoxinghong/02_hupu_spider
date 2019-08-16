# -*- coding: utf-8 -*-
import scrapy


class HupuPost(scrapy.Item):
    post_id = scrapy.Field()
    title = scrapy.Field()
    url = scrapy.Field()
    author = scrapy.Field()
    post_time = scrapy.Field()
    view_count = scrapy.Field()
    reply_count = scrapy.Field()
    content = scrapy.Field()


class HupuPostReply(scrapy.Item):
    reply_id = scrapy.Field()
    author = scrapy.Field()
    post_id = scrapy.Field()
    reply_time = scrapy.Field()
    like_count = scrapy.Field()
    content = scrapy.Field()
    floor_num = scrapy.Field()

