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
        ck_str = "_dacevid3=546a55b5.1910.1efc.19b8.409cb0244ba6; _cnzz_CV30020080=buzi_cookie%7C546a55b5.1910.1efc.19b8.409cb0244ba6%7C-1; __gads=ID=c9f8e895afb8fe55:T=1565833046:S=ALNI_Mat1itzguE982wLzdu8stdkcFnXNQ; PHPSESSID=340ffe7c4b313f98b5af6a5cacab71bd; _HUPUSSOID=40454820-09fd-4431-a126-fa9a873ab464; sensorsdata2015jssdkcross=%7B%22distinct_id%22%3A%2216c92ef8fcc131-0c58b46e246adf-404f012d-1440000-16c92ef8fcd3f2%22%2C%22%24device_id%22%3A%2216c92ef8fcc131-0c58b46e246adf-404f012d-1440000-16c92ef8fcd3f2%22%2C%22props%22%3A%7B%22%24latest_traffic_source_type%22%3A%22%E8%87%AA%E7%84%B6%E6%90%9C%E7%B4%A2%E6%B5%81%E9%87%8F%22%2C%22%24latest_referrer%22%3A%22https%3A%2F%2Fwww.google.com%2F%22%2C%22%24latest_referrer_host%22%3A%22www.google.com%22%2C%22%24latest_search_keyword%22%3A%22%E6%9C%AA%E5%8F%96%E5%88%B0%E5%80%BC%22%7D%7D; lastvisit=0%091566440811%09%2Ferror%2F%40_%40.php%3F; AUM=dgOHQ4Z7c_ux6cpY2vVpu8g3jN5nt-yqlWtWpTno5j7lw; _CLT=868ae16f150cf61ab926af24b4aa60be; u=53388706|6JmO5omRSlIxNjM0MDI4NTkz|eeb4|a2294fb9ee6378c8cbbec7d5a4517294|ee6378c8cbbec7d5|aHVwdV9hZDkyY2M5Yjc0YjgwZDZj; us=e707238c3d9713b658ec3c1f0243d149ad59f98806cb955a4993742a9acb3366c10a4b5e389025b5ac34b76d66fca1a2dee6b2d7ee06621301e0dd76ac516a97; ua=223791296; Hm_lvt_39fc58a7ab8a311f2f6ca4dc1222a96e=1566352556,1566352563,1566523756,1566539086; __dacevst=d36447aa.bd4fa7c4|1566540887415; Hm_lpvt_39fc58a7ab8a311f2f6ca4dc1222a96e=1566539088; _fmdata=nTZqI9WdTrDO%2F1w27lPM9mrZ4UTmR6StR4%2BuRsEubn8EkSHNNZ%2BgS5xNgIJiETKbPETl5HcbHFKYW99vyxDQQ%2B8oCDagvrlsT2C9p0PUj2A%3D"
        cookie_dict = {i.split("=")[0]: i.split("=")[-1] for i in ck_str.split("; ")}

        for i in range(40, int(self.max_page) + 1):
            yield scrapy.Request('http://bbs.hupu.com/vote-' + str(i), cookies=cookie_dict)

    def parse(self, response):
        print(response.url)
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
            print(url)
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
