# -*- coding: utf-8 -*-
BOT_NAME = 'hupu_spider'
SPIDER_MODULES = ['hupu_spider.spiders']
NEWSPIDER_MODULE = 'hupu_spider.spiders'
ROBOTSTXT_OBEY = False


import datetime
to_day = datetime.datetime.now()
log_file_path = "./logs/{}_{}_{}.log".format(to_day.year, to_day.month, to_day.day)
LOG_LEVEL = "INFO"
LOG_FILE = log_file_path

# 配置user_agent的随机类型
RANDOM_UA_TYPE = 'random'

DOWNLOADER_MIDDLEWARES = {
    'hupu_spider.middlewares.RandomUserAgentMiddleware': 543,
    'scrapy.downloadermiddlewares.useragent.UserAgentMiddleware': None,
    # 'hupu_spider.middlewares.ProxyMiddleware': 1,
    # 'hupu_spider.middlewares.ABProxyMiddleware': 1,
    'hupu_spider.middlewares.KDLProxyMiddleware': 1,
}

ITEM_PIPELINES = {
    'hupu_spider.pipelines.HupuSpiderPipeline': 300,
}

# 增加爬虫速度及防ban配置
DOWNLOAD_DELAY = 0
DOWNLOAD_FAIL_ON_DATALOSS = False
CONCURRENT_REQUESTS = 1
CONCURRENT_REQUESTS_PER_DOMAIN = 1
CONCURRENT_REQUESTS_PER_IP = 1
COOKIES_ENABLED = False
DOWNLOAD_TIMEOUT = 10


# msyql数据库配置
MYSQL_HOST = "localhost"
MYSQL_DBNAME = "hupu"
MYSQL_USER = "root"
MYSQL_PASSWD = "lxh123"
MYSQL_PORT = 3306

# redis数据库配置
REDIS_HOST = 'localhost'
REDIS_PORT = 6379
REDIS_PASSWD = "lxh123"
REDIS_DBNAME = 2
REDIS_KEY = "hupu"


#配置自己重写的RFPDupeFilter
DUPEFILTER_CLASS = 'hupu_spider.middlewares.URLRedisFilter'


# 自己的代理池配置
proxy_ip = "106.12.8.109"
proxy_port = 5010

