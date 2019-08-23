# -*- coding: utf-8 -*-
from scrapy import signals
from scrapy.downloadermiddlewares.useragent import UserAgentMiddleware
import random
from scrapy.dupefilters import RFPDupeFilter
import hashlib
import redis
import os
from scrapy.utils.url import canonicalize_url
from hupu_spider import settings
from fake_useragent import UserAgent
import requests
from scrapy.downloadermiddlewares.retry import RetryMiddleware
from scrapy.utils.response import response_status_message
import time
import base64
import json
import logging

logger = logging.getLogger(__name__)


class HupuSpiderSpiderMiddleware(object):
    @classmethod
    def from_crawler(cls, crawler):
        # This method is used by Scrapy to create your spiders.
        s = cls()
        crawler.signals.connect(s.spider_opened, signal=signals.spider_opened)
        return s

    def process_spider_input(self, response, spider):
        # Called for each response that goes through the spider
        # middleware and into the spider.

        # Should return None or raise an exception.
        return None

    def process_spider_output(self, response, result, spider):
        # Called with the results returned from the Spider, after
        # it has processed the response.

        # Must return an iterable of Request, dict or Item objects.
        for i in result:
            yield i

    def process_spider_exception(self, response, exception, spider):
        # Called when a spider or process_spider_input() method
        # (from other spider middleware) raises an exception.

        # Should return either None or an iterable of Response, dict
        # or Item objects.
        pass

    def process_start_requests(self, start_requests, spider):
        # Called with the start requests of the spider, and works
        # similarly to the process_spider_output() method, except
        # that it doesn’t have a response associated.

        # Must return only requests (not items).
        for r in start_requests:
            yield r

    def spider_opened(self, spider):
        spider.logger.info('Spider opened: %s' % spider.name)


class HupuSpiderDownloaderMiddleware(object):
    # Not all methods need to be defined. If a method is not defined,
    # scrapy acts as if the downloader middleware does not modify the
    # passed objects.

    @classmethod
    def from_crawler(cls, crawler):
        # This method is used by Scrapy to create your spiders.
        s = cls()
        crawler.signals.connect(s.spider_opened, signal=signals.spider_opened)
        return s

    def process_request(self, request, spider):
        # Called for each request that goes through the downloader
        # middleware.

        # Must either:
        # - return None: continue processing this request
        # - or return a Response object
        # - or return a Request object
        # - or raise IgnoreRequest: process_exception() methods of
        #   installed downloader middleware will be called
        return None

    def process_response(self, request, response, spider):
        # Called with the response returned from the downloader.

        # Must either;
        # - return a Response object
        # - return a Request object
        # - or raise IgnoreRequest
        return response

    def process_exception(self, request, exception, spider):
        # Called when a download handler or a process_request()
        # (from other downloader middleware) raises an exception.

        # Must either:
        # - return None: continue processing this exception
        # - return a Response object: stops process_exception() chain
        # - return a Request object: stops process_exception() chain
        pass

    def spider_opened(self, spider):
        spider.logger.info('Spider opened: %s' % spider.name)


# 自己定义一个user_agent的类，继承了userAgentMiddleware
class RandomUserAgentMiddleware(object):
    def __init__(self, crawler):
        super(RandomUserAgentMiddleware, self).__init__()
        self.ua = UserAgent()
        # 从setting文件中读取RANDOM_UA_TYPE值
        self.ua_type = crawler.settings.get('RANDOM_UA_TYPE', 'random')

    @classmethod
    def from_crawler(cls, crawler):
        return cls(crawler)

    def process_request(self, request, spider):
        def get_ua():
            '''Gets random UA based on the type setting (random, firefox…)'''
            return getattr(self.ua, self.ua_type)

        user_agent_random = get_ua()
        request.headers.setdefault('User-Agent', user_agent_random)  # 这样就是实现了User-Agent的随即变换


class URLRedisFilter(RFPDupeFilter):
    """ 只根据url去重"""

    def __init__(self, path=None, debug=False):
        RFPDupeFilter.__init__(self, path)
        self.dupefilter = UrlFilterAndAdd()

    def request_seen(self, request):
        # 校验，新增2行代码
        if self.dupefilter.check_url(request.url):
            return True

        # 保留中间页面的去重规则不变，不然爬虫在运行过程中容易出现死循环
        fp = self.request_fingerprint(request)
        if fp in self.fingerprints:
            return True
        self.fingerprints.add(fp)
        if self.file:
            self.file.write(fp + os.linesep)


class UrlFilterAndAdd(object):
    def spider_opened(self, spider):
        return spider.name

    def __init__(self):
        redis_config = {
            "host": settings.REDIS_HOST,
            "port": settings.REDIS_PORT,
            "password": settings.REDIS_PASSWD,
            "db": settings.REDIS_DBNAME,
        }

        pool = redis.ConnectionPool(**redis_config)
        self.pool = pool
        self.redis = redis.StrictRedis(connection_pool=pool)
        self.key = settings.REDIS_KEY

    def url_sha1(self, url):
        fp = hashlib.sha1()
        # 对url中的构成数据进行了重新排列，例如有些url中请求参数一样，但是顺序不同
        fp.update(canonicalize_url(url).encode("utf-8"))
        url_sha1 = fp.hexdigest()
        return url_sha1

    def check_url(self, url):
        # sha1 = self.url_sha1(url)
        # 此处只判断url是否在set中，并不添加url信息，
        # 防止将起始url 、中间url(比如列表页的url地址)写入缓存中
        isExist = self.redis.sismember(self.key, url)
        return isExist

    def add_url(self, url):
        # sha1 = self.url_sha1(url)
        # 将经过hash的url添加到reids的集合中，key为spider_redis_key，命令为SMEMBERS spider_redis_key
        added = self.redis.sadd(self.key, url)
        return added


# 使用自己搭建的代理池，方法一
class ProxyMiddleware(object):
    def process_request(self, request, spider):
        ip_port = requests.get("http://{}:{}/get/".format(settings.proxy_ip, settings.proxy_port)).json().get("proxy")
        request.meta["proxy"] = 'http://' + ip_port
        print(request.meta["proxy"])


# 如果使用的是已经得到的ip list，这时可以使用这个中间件,未完成，需补充才能使用
class MyRetryMiddleware(RetryMiddleware):
    def delete_proxy(self, proxy):
        if proxy:
            # delete proxy from proxies pool
            pass

    def process_response(self, request, response, spider):
        if request.meta.get('dont_retry', False):
            return response
        if response.status in self.retry_http_codes:
            reason = response_status_message(response.status)
            # 删除该代理
            self.delete_proxy(request.meta.get('proxy', False))
            time.sleep(random.randint(3, 5))
            self.logger.warning('返回值异常, 进行重试...')
            return self._retry(request, reason, spider) or response
        return response

    def process_exception(self, request, exception, spider):
        if isinstance(exception, self.EXCEPTIONS_TO_RETRY) \
                and not request.meta.get('dont_retry', False):
            # 删除该代理
            self.delete_proxy(request.meta.get('proxy', False))
            time.sleep(random.randint(3, 5))
            self.logger.warning('连接异常, 进行重试...')
            return self._retry(request, exception, spider)


""" 阿布云代理配置"""


class ABProxyMiddleware(object):
    """ 阿布云ip代理配置 """
    proxyServer = "http://http-dyn.abuyun.com:9020"
    proxyUser = "xxx"
    proxyPass = "xxx"
    proxyAuth = "Basic " + base64.urlsafe_b64encode(bytes((proxyUser + ":" + proxyPass), "ascii")).decode("utf8")

    def process_request(self, request, spider):
        request.meta["proxy"] = self.proxyServer
        request.headers["Proxy-Authorization"] = self.proxyAuth


def fetch_one_proxy():
    """
        提取一个代理
    """
    orderid = '906652644621628'  # 订单号
    # 提取代理链接，以私密代理为例
    api_url = "https://dps.kdlapi.com/api/getdps/?orderid={}&num=1&pt=1&format=json&sep=1"
    fetch_url = api_url.format(orderid)
    r = requests.get(fetch_url)
    if r.status_code != 200:
        logger.error("fail to fetch proxy")
        return False
    content = json.loads(r.content.decode('utf-8'))
    ips = content['data']['proxy_list']
    return ips[0]


# 快代理非开放代理且未添加白名单，需用户名密码认证
username = "767166726"
password = "xxx"
proxy = fetch_one_proxy()  # 获取一个代理
THRESHOLD = 2  # 换ip阈值
fail_time = 0  # 此ip异常次数


class KDLProxyMiddleware(object):
    def process_request(self, request, spider):
        proxy_url = 'http://%s:%s@%s' % (username, password, proxy)
        request.meta['proxy'] = proxy_url
        auth = "Basic %s" % (base64.b64encode(('%s:%s' % (username, password)).encode('utf-8'))).decode('utf-8')
        request.headers['Proxy-Authorization'] = auth

    def process_response(self, request, response, spider):
        global fail_time, proxy, THRESHOLD
        if not (200 <= response.status < 300):
            fail_time += 1
            if fail_time >= THRESHOLD:
                proxy = fetch_one_proxy()
                fail_time = 0
        return response


if __name__ == "__main__":
    for i in range(100):
        proxy = fetch_one_proxy()
        proxy_url = 'http://%s:%s@%s' % (username, password, proxy)
        headers = {}
        auth = "Basic %s" % (base64.b64encode(('%s:%s' % (username, password)).encode('utf-8'))).decode('utf-8')
        headers['Proxy-Authorization'] = auth
        print(requests.get("https://bbs.hupu.com/vote-2", headers=headers, proxies={"http": proxy_url}).text)
