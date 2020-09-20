# coding : utf-8
import requests
from urllib.parse import urlparse
from urllib.parse import urljoin
import re
import os
import hashlib


def get_html(url):
    try:
        par = urlparse(url)
        Default_Header = {'X-Requested-With': 'XMLHttpRequest',
                          'Referer': par[0] + '://' + par[1],
                          'User-Agent': 'Mozilla/5.0 (Windows NT 6.3; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/54.0.2840.87 Safari/537.36',
                          'Host': par[1]}
        html = requests.get(url, headers=Default_Header, timeout=10)
        if html.status_code != 200:
            return None
        return html.content
    except Exception as e:
        print("get_html error--", e)
        return None


def full_link(url1, url2, flag_site=True):
    try:
        if url2[0] == '#':
            return None
        filepat = re.compile(r'(.*?)\.(.*?)')
        htmpat = re.compile(r'(.*?)\.htm$|(.*?)\.html$|(.*?)\.php$|(.*?)\.aspx$')
        u1 = urlparse(url1)
        if filepat.match(u1.path) and not htmpat.match(u1.path):
            return None
        if url1[-1] == '/':
            url1 = url1 + "index.html"
        elif filepat.match(u1.path) is None:
            url1 = url1 + "/index.html"
        url2 = urljoin(url1, url2)
        u2 = urlparse(url2)
        if u1.netloc != u2.netloc and flag_site:
            return None
        return url2

    except Exception as e:
        print("full_link error--", e)
        return None


def md5_url(url):
    obj = hashlib.md5()
    obj.update(bytes(url, encoding='utf-8'))
    return obj.hexdigest() + ".html"


def save_html(url):
    dir_name = urlparse(url).netloc
    # 建立url所需要的目录
    os.makedirs(dir_name, exist_ok=True)
    html = get_html(url)
    html_file_name = md5_url(url)
    if html is not None:
        with open(os.path.join(dir_name, html_file_name), 'wb') as f:
            f.write(html)
    return html
