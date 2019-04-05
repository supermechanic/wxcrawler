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
    req_count = 0
    # 从redis读取url message queue
    def __init__(self, cookie_pool, proxy_pool):
        self.url_key = "urls"
        self.cookie_pool = cookie_pool
        self.proxy_pool = proxy_pool

    def get_page_source(self, url):
        page_source = requests.get(url, cookies=self.current_cookie,
                                  proxies=self.current_proxy, headers=header).content
        return page_source

    def parse_account(self, content):
        bsObj = BeautifulSoup(
            str(content, encoding="utf-8"), "html.parser")
        
    def run(self):
        while True:
            #从队列中获取一个待爬取url
            current_url = r.blpop(self.url_key, timeout=2)
            if (req_count >= 20):
                #随机从池子中选取一个cookie和代理
                self.current_cookie = self.cookie_pool[1]
                self.current_proxy = self.proxy_pool[1]
            content = self.get_page_source(current_url)
            req_count += 1
            #每爬取一个页面，停10s
            time.sleep(10)

class ArticlesDownloader:
    pass


def main(keys):
    pool1 = cookie_pool.get_n_cookies(2)
    pool2 = ip_pool.get_proxy_list()#获取可用代理列表
    spider = WXAccountsSpider(keys, pool[0])  # 暂时只使用一个spider
    spider.run()
    downloader = AccountsDownloader()
    


if __name__ == "__main__":
    key_list = ["女性", "美妆", "时尚", "女性健康", "穿搭", "星座"， "少女"， "穿衣"， "fashion"]
    main(key_list)
