# -*- coding: utf-8 -*-
import re
import time
import copy
import scrapy
import logging
from hupu_spider.items import HupuPost, HupuPostReply


class HupuPostSpider(scrapy.Spider):
    name = 'hupu_post'
    allowed_domains = ['bbs.hupu.com']
    page_compile = re.compile("^.*pageCount:(\d+)", re.S)

    def __init__(self, category=None, *args, **kwargs):
        super(HupuPostSpider, self).__init__(*args, **kwargs)
        self.max_page = kwargs.get("max_page", 5000)

    def start_requests(self):
        for i in range(1, int(self.max_page) + 1):
            yield scrapy.Request('http://bbs.hupu.com/vote-' + str(i))

    def parse(self, response):
        for li in response.xpath('//ul[@class="for-list"]/li'):
            title_href = li.xpath(".//a[@class='truetit']/@href").extract_first()
            url = "https://bbs.hupu.com" + title_href
            post_id = self.get_post_id(title_href)
            title = li.xpath(".//a[@class='truetit']/text()").extract_first()
            author = li.xpath(".//a[@class='aulink']/text()").extract_first()
            post_time = li.xpath(".//a[@style='color:#808080;cursor: initial; ']/text()").extract_first()
            count_des = li.xpath(".//span[@class='ansour box']/text()").extract_first()
            reply_count = re.match('(\d+)[^0-9]*(\d+)', count_des).group(1)
            view_count = re.match('(\d+)[^0-9]*(\d+)', count_des).group(2)

            post_item = {"post_id": post_id, "title": title, "url": url, "author": author, "post_time": post_time,
                         "view_count": view_count, "reply_count": reply_count}
            yield scrapy.Request(url, self.post_content_parse, meta=post_item, dont_filter=True)

    def post_content_parse(self, response):
        print(response.url)
        post_item = copy.deepcopy(response.meta)
        page_match = self.page_compile.match(response.text)
        total_pages = 1
        if page_match is not None:
            total_pages = int(page_match.group(1))
        contents = response.xpath("//div[@class='quote-content']//p/text()").extract()
        content = "".join([i.strip() for i in contents])

        post_detailt_time = response.xpath("//div[@class='floor-show']//span[@class='stime']/text()").extract_first()
        post_id = self.get_post_id(response.url)

        item = HupuPost()
        item['post_id'] = post_item["post_id"]
        item['title'] = post_item["title"]
        item['url'] = post_item["url"]
        item['author'] = post_item["author"]
        item['post_time'] = post_item["post_time"]
        item['view_count'] = post_item["view_count"]
        item['reply_count'] = post_item["reply_count"]
        item['content'] = content
        yield item

        for reply in response.xpath("//div[@class='floor']"):
            if reply.xpath("@id") is None:
                continue
            hupu_reply_id = reply.xpath("@id").extract_first()
            floor_num = reply.xpath(".//a[@class='floornum']/@id").extract_first()
            if hupu_reply_id == "tpc" or floor_num is None:
                continue
            author = reply.xpath(".//div[@class='author']//a[@class='u']/text()").extract_first()
            reply_time = reply.xpath(".//div[@class='author']//span[@class='stime']/text()").extract_first()
            like_count = reply.xpath(
                ".//div[@class='author']//span[@class='ilike_icon_list']//span[@class='stime']/text()").extract_first()
            contents = reply.xpath(".//tbody//td//text()").extract()
            # content = "".join([i.strip() for i in contents])
            content = self.parse_content(contents)

            reply_item = HupuPostReply()
            reply_item["reply_id"] = hupu_reply_id
            reply_item["author"] = author
            reply_item["post_id"] = post_item["post_id"]
            reply_item["reply_time"] = reply_time
            reply_item["like_count"] = like_count
            reply_item["content"] = content
            reply_item["floor_num"] = floor_num

            yield reply_item

            if total_pages > 1:
                for page in range(2, total_pages + 1):
                    url = "https://bbs.hupu.com/%s-%s.html" % (post_id, page)
                    scrapy.Request(url, self.after_the_first_page_reply, dont_filter=True)

    def after_the_first_page_reply(self, response):
        post_id = self.get_post_id(response.url)
        for reply in response.xpath("//div[@class='floor']"):
            if reply.xpath("@id") is None:
                continue
            hupu_reply_id = reply.xpath("@id").extract_first()
            if hupu_reply_id == "tpc":
                continue
            author = reply.xpath(".//div[@class='author']//a[@class='u']/text()").extract_first()
            reply_time = reply.xpath(".//div[@class='author']//span[@class='stime']/text()").extract_first()
            like_count = reply.xpath(
                ".//div[@class='author']//span[@class='ilike_icon_list']//span[@class='stime']/text()").extract_first()
            contents = reply.xpath(".//tbody//td//text()").extract()
            # content = "".join([i.strip() for i in contents])
            content = self.parse_content(contents)

            floor_num = reply.xpath(".//a[@class='floornum']/@id").extract_first()

            reply_item = HupuPostReply()
            reply_item["reply_id"] = hupu_reply_id
            reply_item["author"] = author
            reply_item["post_id"] = post_id
            reply_item["reply_time"] = reply_time
            reply_item["like_count"] = like_count
            reply_item["content"] = content
            reply_item["floor_num"] = floor_num
            yield reply_item

    @staticmethod
    def get_post_id(url):
        return re.match('[^0-9]*(\d+)', url).group(1)

    @staticmethod
    def parse_content(contents):
        content = ""
        if "引用 @" in contents:
            contents.insert(-4, "======")

        for con in contents:
            if con == "":
                continue
            sendmatch = re.match("^发自", con)
            if sendmatch is not None:
                continue
            modifiedmatch = re.match("修改", con)
            if modifiedmatch is not None:
                continue
            content += con.strip()
        return content
