# -*- coding: UTF-8 -*-
from urllib import parse
import requests
import re

class WXAccountsSpider:
    urlCount = 0
    # 获取URL列表只通过，一个cookie，不使用代理，不加cookie只显示10页内容

    def __init__(self, keys, cookie, proxies):
        self.name = "微信爬虫"
        self.keys = keys
        self.urlListKey = "urls"
        self.cookie = cookie
        self.proxy = proxies
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
        pageSource = requests.get(
            url, cookies=self.cookie, headers=header).content
        bsObj = BeautifulSoup(
            str(pageSource, encoding="utf-8"), "html.parser")
        # print(bsObj)
        if(bsObj == None):
            return 0
        itemCountText = bsObj.find("div", {"class": "mun"}).text
        pattern = re.compile(r'\d+')
        itemCount = pattern.findall(itemCountText.replace(",", ""))[0]
        pageCount = int(int(itemCount)/10) + 1
        return pageCount

    def run(self):
        for keyWord in self.keys:
            page1 = self.genUrl(keyWord, 1)  # 获取第一页
            count = self.getTotalPage(page1)
            print(count)
            if (count < 2):
                continue
            for i in range(2, count+1):
                self.genUrl(keyWord, i)
