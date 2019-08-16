# -*- coding: utf-8 -*-
from scrapy.exceptions import DropItem
from scrapy import Request
import pymysql
import time
from scrapy.pipelines.images import ImagesPipeline
from twisted.enterprise import adbapi
from hupu_spider.items import HupuPost, HupuPostReply
from hupu_spider.middlewares import UrlFilterAndAdd, URLRedisFilter

import logging
logger = logging.getLogger(__name__)


class HupuSpiderPipeline(object):
    post_sql_str = """insert into hupu_post(post_id,title,url,author,post_time,view_count,reply_count,content) values ("{post_id}","{title}","{url}","{author}","{post_time}","{view_count}","{reply_count}","{content}");"""

    reply_sql_str = """insert into hupu_post_reply(reply_id,author,post_id,reply_time,like_count,floor_num,content) values ("{reply_id}","{author}","{post_id}","{reply_time}","{like_count}","{floor_num}","{content}");"""

    def __init__(self, pool):
        self.dupefilter = UrlFilterAndAdd()
        self.dbpool = pool

    @classmethod
    def from_settings(cls, settings):
        dbparms = dict(
            host=settings.get("MYSQL_HOST"),
            port=settings.get("MYSQL_PORT"),
            db=settings.get("MYSQL_DBNAME"),
            user=settings.get("MYSQL_USER"),
            passwd=settings.get("MYSQL_PASSWD"),
            charset='utf8mb4',
            cursorclass=pymysql.cursors.DictCursor,
            use_unicode=True
        )
        dbpool = adbapi.ConnectionPool("pymysql", **dbparms)
        return cls(dbpool)

    def process_item(self, item, spider):
        if isinstance(item, HupuPost):
            self.dupefilter.add_url(item['url'])
            query = self.dbpool.runInteraction(self.do_insert_post, item)
            query.addErrback(self.handle_error, item, spider)

        elif isinstance(item, HupuPostReply):
            query = self.dbpool.runInteraction(self.do_insert_reply, item)
            query.addErrback(self.handle_error, item, spider)

    def handle_error(self, failure, item, spider):
        logger.warning("数据库插入异常===" + str(failure))

    def do_insert_post(self, cursor, item):
        # 执行具体的插入
        # 根据不同的item 构建不同的sql语句并插入到mysql中
        sqltext = self.post_sql_str.format(
            post_id=item["post_id"],
            title=pymysql.escape_string(str(item["title"])),
            url=pymysql.escape_string(str(item["url"])),
            author=pymysql.escape_string(str(item["author"])),
            post_time=pymysql.escape_string(str(item["post_time"])),
            view_count=item["view_count"],
            reply_count=item["reply_count"],
            content=pymysql.escape_string(str(item["content"]))
        )
        cursor.execute(sqltext)

    def do_insert_reply(self, cursor, item):
        sqltext = self.reply_sql_str.format(
            reply_id=item["reply_id"],
            author=pymysql.escape_string(str(item["author"])),
            post_id=item["post_id"],
            reply_time=pymysql.escape_string(str(item["reply_time"])),
            like_count=item["like_count"],
            floor_num=item["floor_num"],
            content=pymysql.escape_string(str(item["content"]))
        )
        cursor.execute(sqltext)

    def close_spider(self, spider):
        self.cursor.close()
        self.connect.close()
