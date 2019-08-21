# -*- coding: utf-8 -*-
import re
import time
import copy
import logging
import requests
import utils
from urllib.parse import urlencode

index_url = "https://bbs.mobileapi.hupu.com/1/7.3.17/topics"
client = utils.get_random_client(),
params = {
    'all': '1',
    'clientId': utils.get_random_clientId(),
    'crt': int(time.time() * 1000),
    'night': '0',
    'client': client,
    '_ssid': utils.get_random_ssid(),
    '_imei': utils.get_random_imei(),
    'time_zone': 'Asia/Shanghai',
    'android_id': client,
}
params["sign"] = utils.get_sign(params)

url = index_url + "?" + urlencode(params)

print(requests.get(url))