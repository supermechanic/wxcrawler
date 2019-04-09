# -*- coding: UTF-8 -*-
from urllib import parse
from bs4 import BeautifulSoup
import requests
import re
import redis_conn

header = {
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3",
    'Accept-Encoding': 'gzip, deflate',
    'Accept-Language': 'zh-CN,zh;q=0.9',
    'Connection': 'keep-alive',
    'Host': 'weixin.sogou.com',
    'Upgrade-Insecure-Requests': '1',
    'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/73.0.3683.103 Safari/537.36',
}
r = redis_conn.getRedisConn()


class WXAccountsSpider:
    urlCount = 0
    # 获取URL列表只通过，一个cookie，不使用代理，不加cookie只显示10页内容

    def __init__(self, keys, cookies, proxies):
        self.name = "微信爬虫"
        self.keys = keys
        self.urlListKey = "urls"
        self.cookies = cookies
        self.proxies = proxies
        self.current_cookie_index = 0
        self.current_proxy_index = 0
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
        response = requests.get(
            url, cookies=self.cookies[self.current_cookie_index], proxies=self.proxies[self.current_proxy_index], headers=header)
        if response.status_code == 200:
            print("REQUEST OK!")
            page_source = response.content
        elif response.status_code == 302:
            # TODO 需要弹出验证码页面，并更新cookie
            self.current_cookie_index = (
                self.current_cookie_index + 1) % len(self.cookies)

        else:
            print('切换cookie')
            self.current_cookie_index = (
                self.current_cookie_index + 1) % len(self.cookies)
            r.rpush("urls", url)
        bsObj = BeautifulSoup(
            str(page_source, encoding="utf-8"), "html.parser")
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


class WXArticleSpider:
    pass


class We123Spiderf:
    pass
