# -*- coding: UTF-8 -*-
from selenium import webdriver
from http import cookiejar
from urllib import parse
from urllib import request
from bs4 import BeautifulSoup
import re
import redis
import time
import ip_pool
import cookie_pool
import requests

header = {
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8',
    'Accept-Encoding': 'gzip, deflate',
    'Accept-Language': 'zh-CN,zh;q=0.9',
    'Connection': 'keep-alive',
    'Host': 'weixin.sogou.com',
    'Upgrade-Insecure-Requests': '1',
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/62.0.3202.94 Safari/537.36',
}

global r
r = newRedisConn()


def newRedisConn(host="127.0.0.1", port=6379):
    return redis.Redis(host=host, port=port)


def getRedisConn():
    return r


def Json2WXAccount(info):
    return WXAccount(wxid=info["wxid"], authName=info["authName"], description=info["description"])


class WXAccount:
    def __init__(self, wxid, authName, description):
        self.wxid = wxid
        self.authName = authName
        self.description = description

    def toJson(self):
        return {
            "wxid": self.wxid,
            "authName": self.authName,
            "description": self.description
        }


class WXAccountsSpider:
    urlCount = 0
    # 获取URL列表只通过，一个cookie，不使用代理，不加cookie只显示10页内容

    def __init__(self, keys, cookie):
        self.name = "微信爬虫"
        self.keys = keys
        self.urlListKey = "urls"
        self.cookie = cookie
        self.reqParam = {
            "query": "",  # 搜索关键词
            "_sug": "n",
            "_sug_type": "",
            "s_from": "input",
            "type": "1",  # 1代表搜索公众号，2代表搜索文章
            "page": "1",  # 页码
            "ie": "utf8",
            "w": "",
            "sut": 0,
            "sst0": 0,
            "lkt": "",
        }

    def genUrl(self, key, pageNo):
        self.reqParam["query"] = key
        self.reqParam["page"] = pageNo
        url = "https://weixin.sogou.com/weixin?" + \
            parse.urlencode(self.reqParam)
        print(url)
        r.lpush(self.urlListKey, url)
        WXAccountsSpider.urlCount += 1
        return url

    def getTotalPage(self, url):
        pageSource = requests.get(url, cookies=self.cookie,
                                  headers=header).content
        bsObj = BeautifulSoup(
            str(pageSource, encoding="utf-8"), "html.parser")
        itemCountText = bsObj.find("div", {"class": "mun"}).text
        pattern = re.compile(r'\d+')
        itemCount = pattern.findall(itemCountText.replace(",", ""))[0]
        pageCount = int(int(itemCount)/10)
        return pageCount

    def run(self):
        for keyWord in self.keys:
            page1 = self.genUrl(keyWord, 1)  # 获取第一页
            count = self.getTotalPage(page1)
            if (count < 2):
                continue
            for i in range(2, count):
                self.genUrl(keyWord, i)


class AccountsDownloader:
    # 从redis读取url message queue
    pass


class ArticlesDownloader:
    pass


def main(keys):
    pool = cookie_pool.CookiesPool()
    i = 0
    while i < 2:
        pool.genCookie()
        i += 1
    spider = WXAccountsSpider(keys, pool.get_one_cookie())  # 暂时只使用一个spider
    spider.run()


if __name__ == "__main__":
    key_list = ["女性", "美妆", "时尚", "女性健康", "穿搭", "星座"]
    main(key_list)
