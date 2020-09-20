# -*- coding: UTF-8 -*-
import queue
import tools
import math
from lxml import etree
import time
import click


@click.command()
@click.option('--flag_site', default=2, help='flag_site参数（1.全网抓取；2.站内抓取），默认全站', type=int)
@click.option('--flag_most', default=-1, help='flag_most参数最大网页抓取个数，无穷大请输入-1，默认无穷大', type=int)
@click.option('--flag_depth', default=-1, help='flag_depth参数宽度优先搜索最大抓取深度，无穷大请输入-1,默认无穷大', type=int)
def site_crawl(flag_site, flag_most, flag_depth):
    domain_urls = []
    with open('domain_urls.txt', 'r') as f:
        for line in f.readlines():
            if line != '\n':
                domain_urls.append(line.replace('\n', ''))
    pool = set()
    q = queue.Queue()
    for i in domain_urls:
        if i not in pool:
            pool.add(i)
            q.put((i.strip(), 1))
    if flag_site == 1:
        flag_site = False
    else:
        flag_site = True
    if flag_most == -1:
        flag_most = math.inf
    else:
        flag_most = int(flag_most)
    if flag_depth == -1:
        flag_depth = math.inf
    else:
        flag_depth = int(flag_depth)

    now = 0
    while not q.empty():
        try:
            front = q.get()
            domain_url = front[0]
            depth = front[1]
            print('crawling:', domain_url)
            html = tools.save_html(domain_url)
            if html is None:
                continue
            for url in etree.HTML(html).xpath("//a/@href"):
                try:
                    full_url = tools.full_link(domain_url, url, flag_site)
                    if full_url is None:
                        continue
                    if (full_url not in pool) and (depth + 1 <= flag_depth):
                        pool.add(full_url)
                        q.put((full_url, depth + 1))
                except Exception as e:
                    print("full_url error-----", e)
            now += 1
            if now >= flag_most:
                break
        except Exception as e:
            print("main error---", e)


if __name__ == '__main__':
    site_crawl()
