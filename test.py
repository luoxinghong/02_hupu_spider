# -*- coding: utf-8 -*-
import re
import time
import copy
import logging
import requests

url = "https://bbs.hupu.com/vote-2"
proxies = {
    "http": "http://http://80.106.247.145:53410",
}
headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/65.0.3325.181 Safari/537.36",
}

print(requests.get(url, headers=headers, proxies=proxies).text)
