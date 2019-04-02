# -*- coding: UTF-8 -*-
from http import cookiejar
from urllib import parse
from urllib import request
import redis

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


class CookiesPool:
    def __init__(self):
        pass

    def getCookie(self):
        pass

    def addCookie(self, cookie):
        pass


class WXAccountsSpider:
    urlCount = 0

    def __init__(self, keys):
        self.name = "微信爬虫"
        self.keys = keys
        self.urlListKey = "urls"
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
        request.urlopen()
        return 2

    def run(self):
        for keyWord in self.keys:
            page1 = self.genUrl(keyWord, 1)  # 获取第一页
            count = self.getTotalPage(page1)
            if (count < 2):
                continue
            for i in range(2, count):
                self.genUrl(keyWord, i)


class AccountsDownloader:
    pass


class ArticlesDownloader:
    pass


if __name__ == "__main__":
    key_list = ["女性", "美妆", "时尚", "女性健康", "穿搭", "星座"]
