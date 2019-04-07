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
import requests
import csv
import random

header = {
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3",
    'Accept-Encoding': 'gzip, deflate',
    'Accept-Language': 'zh-CN,zh;q=0.9',
    'Connection': 'keep-alive',
    'Host': 'weixin.sogou.com',
    'Upgrade-Insecure-Requests': '1',
    'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/73.0.3683.103 Safari/537.36',
}

def newRedisConn(host="127.0.0.1", port=6379):
    return redis.Redis(host=host, port=port)

global r
r = newRedisConn()


def getRedisConn():
    return r


class WXAccount:
    def __init__(self, wxid='', wxname='', authName='', description=''):
        self.wxid = wxid #微信id
        self.wxname = wxname#微信名
        self.authName = authName#认证名称，多为公司名
        self.description = description#公众号描述
    def toJson(self):
        return {
            "wxid": self.wxid,
            "wxname": self.wxname,
            "authName": self.authName,
            "description": self.description
        }
    def save2csv(self):
        #以逗号方式分割加换行符
        #temp = self.wxid+","+self.wxname +","+ self.authName +","+ self.description
        row = [self.wxid, self.wxname, self.authName, self.description]
        with open('data.csv', 'w', newline='') as f:
            writer = csv.writer(f)
            writer.writerow(row)

    def save2db(self, db_conn):
        #保存到数据库中
        pass

def Json2WXAccount(info):
    return WXAccount(wxid=info["wxid"], wxname=info["wxname"],authName=info["authName"], description=info["description"])

class WXAccountsSpider:
    urlCount = 0
    # 获取URL列表只通过，一个cookie，不使用代理，不加cookie只显示10页内容

    def __init__(self, keys, cookie, proxies):
        self.name = "微信爬虫"
        self.keys = keys
        self.urlListKey = "urls"
        self.cookie = cookie
        self.proxies = proxies
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
        pageSource = requests.get(url,cookies=self.cookie, proxies=self.proxies, headers=header).content
        print(pageSource)
        bsObj = BeautifulSoup(
            str(pageSource, encoding="utf-8"), "html.parser")
        print(bsObj)
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


class AccountsDownloader:
    req_count = 0
    # 从redis读取url message queue
    def __init__(self, cookie_pool, proxy_pool):
        self.url_key = "urls"
        self.cookie_pool = cookie_pool
        self.proxy_pool = proxy_pool
        self.current_cookie = cookie_pool[0]
        self.current_proxy = proxy_pool[0]


    def get_page_source(self, url):
        print("正在请求的地址"+url)
        print(self.current_proxy)
        print(self.current_cookie)
        page_source = requests.get(url, cookies=self.current_cookie,
                                  proxies=self.current_proxy, headers=header).content
        return page_source

    def parse_account(self, content):
        bsObj = BeautifulSoup(
            str(content, encoding="utf-8"), "html.parser")
        divs = bsObj.find_all("li",{"id":re.compile("sogou_vr_*")})
        for child in divs:
            id = child.find("label", {"name": "em_weixinhao"}).text
            name = child.find("a", {"uigs": re.compile("account_name_*")}).text
            account = WXAccount(wxid=id, wxname=name)
            account.save2csv()
        
    def run(self):
        while True:
            #从队列中获取一个待爬取url
            obj = r.brpop(self.url_key, timeout=2)
            current_url = obj[1].decode('utf-8')
            if (self.req_count >= 20):
                #随机从池子中选取一个cookie和代理
                self.current_cookie = self.cookie_pool[random.randint(0, len(self.cookie_pool))]
                self.current_proxy = self.proxy_pool[random.randint(0, len(self.proxy_pool))]
            content = self.get_page_source(current_url)
            self.parse_account(content)
            self.req_count += 1
            #每爬取一个页面，停10s
            time.sleep(10)

class ArticlesDownloader:
    pass

def main(keys):
    pool1 = [{'ppmdig': '15546432140000004a323c0d54f5b27b9291b4d9aa1eeb9b', 'sgid': '28-34275857-AVypibQ5pCBA6dibsNpz5VYicY', 'pprdig': 'ULVGPvRrTCpePR9H_ZT2eXO-TgSfMbaGnSPi-pMqwVGw20-UlJUZUZrCMyIXoRxOlohZUnd0vm6cUeP9zcGZEkYf5kMAHCcgMqmrWvRc2miS52jmVKogFlc9cRWF-6vuYGELwqbNjdLIOZnYJuC-gGgmbhKokDIm-b0wPJyf9_A', 'ppinf': '5|1554643214|1555852814|dHJ1c3Q6MToxfGNsaWVudGlkOjQ6MjAxN3x1bmlxbmFtZToyNzolRTYlOUMlQkElRTYlQTIlQjAlRTUlQjglODh8Y3J0OjEwOjE1NTQ2NDMyMTR8cmVmbmljazoyNzolRTYlOUMlQkElRTYlQTIlQjAlRTUlQjglODh8dXNlcmlkOjQ0Om85dDJsdUdQeEx0dk92U1pBVG5xVjNvYk9tOG9Ad2VpeGluLnNvaHUuY29tfA', 'SUV': '0077EACF7B7434015CA9F90AB923A772', 'SUID': '0134747B4631990A000000005CA9F907', 'weixinIndexVisited': '1', 'IPLOC': 'CN1100', 'ABTEST': '8|1554643207|v1'}, {'ppmdig': '15546432320000005f548f95c22a3584bb8b8d5d21e43308', 'sgid': '14-39976631-AVypibSBPgUZvMiaor5czcuM0', 'pprdig': 'ZAQAppVJb8iW4aLX1isiM9B5OHrOGeQzxtxKjHFneAG4Z7oc0S6Vbp3iOk_qHSaA0PqC5RrRPlKeHrpGT3yfWOFqarTX-RzeMW6kqdSb7XztzHy7_HQvPFLkbtPuenRWxDN2M3n0ed2Rdcj2wGFT3jhBFzdPXSpSVwkhnZ4ZKwE', 'ppinf': '5|1554643232|1555852832|dHJ1c3Q6MToxfGNsaWVudGlkOjQ6MjAxN3x1bmlxbmFtZToxODolRTQlQjglQkUlRTQlQjglQUF8Y3J0OjEwOjE1NTQ2NDMyMzJ8cmVmbmljazoxODolRTQlQjglQkUlRTQlQjglQUF8dXNlcmlkOjQ0Om85dDJsdUtmNjJWLXNDU01rNjJMaFZkS1hoWGNAd2VpeGluLnNvaHUuY29tfA', 'SUV': '00B9EAD57B7434015CA9F91CBA0A7716', 'SUID': '0134747B4631990A000000005CA9F91A', 'weixinIndexVisited': '1', 'IPLOC': 'CN1100', 'ABTEST': '6|1554643226|v1'}]
    pool2 = [{'https':'http://222.135.92.68:38094'},{'https':'http://110.52.235.137:9999'},{'https':'http://110.52.235.2:9999'}]
    spider = WXAccountsSpider(keys, pool1[1], pool2[0])  # 暂时只使用一个spider
    spider.run()
    downloader = AccountsDownloader(pool1, pool2)
    downloader.run()
    
if __name__ == "__main__":
    key_list = ["女性", "时尚", "女性健康", "星座", "少女", "穿衣", "fashion"]
    main(key_list)
