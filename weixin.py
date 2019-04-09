# -*- coding: UTF-8 -*-
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
import json
import random
import spider
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


class WXAccount:
    def __init__(self, wxid='', wxname='', authName='', description=''):
        self.wxid = wxid  # 微信id
        self.wxname = wxname  # 微信名
        self.authName = authName  # 认证名称，多为公司名
        self.description = description  # 公众号描述

    def toJson(self):
        jsondata = json.dumps({
            "wxid": self.wxid,
            "wxname": self.wxname,
            "authName": self.authName,
            "description": self.description
        }, indent=4)
        print(jsondata)
        return jsondata

    def save2redis(self):
        data = self.toJson()
        r.hset("accouts", self.wxid, data)

    def save2csv(self):
        # 以逗号方式分割加换行符
        # temp = self.wxid+","+self.wxname +","+ self.authName +","+ self.description
        row = [self.wxid, self.wxname, self.authName, self.description]
        with open('data.csv', 'a', newline='') as f:
            writer = csv.writer(f)
            writer.writerow(row)

    def save2db(self, db_conn):
        # 保存到数据库中
        pass


def Json2WXAccount(info):
    return WXAccount(wxid=info["wxid"], wxname=info["wxname"], authName=info["authName"], description=info["description"])


class AccountsDownloader:
    req_count = 0
    # 从redis读取url message queue

    def __init__(self, cookie_pool, proxy_pool):
        self.url_key = "urls"
        self.cookie_pool = cookie_pool
        self.proxy_pool = proxy_pool
        self.current_cookie = cookie_pool[0]
        self.current_proxy = proxy_pool[0]

    def unlock(self, antiurl):
        oldcookies = self.current_cookie
        retries = 0
        while retries < 3:
            tc = int(round(time.time() * 1000))
            captcha = requests.get(
                'http://weixin.sogou.com/antispider/util/seccode.php?tc={}'.format(tc), cookies=oldcookies)

            with open('captcha.jpg', 'wb') as file:
                file.write(captcha.content)

            c = input("请输入captcha.jpg中的验证码:")

            thank_url = 'http://weixin.sogou.com/antispider/thank.php'
            formdata = {
                'c': c,
                'r': '%2F' + antiurl,
                'v': 5
            }
            headers = {
                'Content-Type': 'application/x-www-form-urlencoded; charset=UTF-8',
                'Referer': 'http://weixin.sogou.com/antispider/?from=%2f' + antiurl
            }

            resp = requests.post(thank_url, data=formdata,
                                 headers=headers, cookies=oldcookies)

            resp = json.loads(resp.text)

            if resp.get('code') != 0:
                print("解锁失败。重试次数:{0:d}".format(3-retries))
                retries += 1
                continue

            oldcookies['SNUID'] = resp.get('id')
            oldcookies['SUV'] = '00D80B85458CAE4B5B299A407EA3A580'
            # print ("更新Cookies。", oldcookies)
            self.current_cookie = oldcookies

    def get_page_source(self, url):
        print("正在请求的地址--"+url)
        response = requests.get(
            url, cookies=self.current_cookie, proxies=self.current_proxy, headers=header)
        if response.status_code == 200:
            print("RESPONSE OK!")
            return response.content
        elif response.status_code == 302:
            print("需要弹出验证码页面，并更新cookie")
            self.unlock(url)
            r.rpush(self.url_key, url)
            return None
        else:
            print('切换cookie')
            self.current_cookie = self.cookie_pool[random.randint(
                0, len(self.cookie_pool)-1)]
            return None

    def parse_account(self, content):
        print(content)
        bsObj = BeautifulSoup(
            str(content, encoding="utf-8"), "html.parser")
        divs = bsObj.find_all("li", {"id": re.compile("sogou_vr_*")})
        for child in divs:
            id = child.find("label", {"name": "em_weixinhao"}).text
            name = child.find("a", {"uigs": re.compile("account_name_*")}).text
            account = WXAccount(wxid=id, wxname=name)
            account.save2redis()
            account.save2csv()
            print(account)

    def run(self):
        while True:
            # 从队列中获取一个待爬取url
            obj = r.brpop(self.url_key, timeout=5)
            if(obj == None):
                print("没有更多数据，程序退出")
                return
            current_url = obj[1].decode('utf-8')
            if (self.req_count >= 20):
                # 随机从池子中选取一个cookie和代理
                self.current_cookie = self.cookie_pool[random.randint(
                    0, len(self.cookie_pool)-1)]
                self.current_proxy = self.proxy_pool[random.randint(
                    0, len(self.proxy_pool))]
                self.req_count = 0
            content = self.get_page_source(current_url)
            if content == None:
                print("获取页面失败")
                continue
            self.parse_account(content)
            self.req_count += 1
            # 每爬取一个页面，停9s
            time.sleep(9)


class ArticlesDownloader:
    pass


def main(keys):
    pool1 = [{'ppmdig': '15546432140000004a323c0d54f5b27b9291b4d9aa1eeb9b', 'sgid': '28-34275857-AVypibQ5pCBA6dibsNpz5VYicY', 'pprdig': 'ULVGPvRrTCpePR9H_ZT2eXO-TgSfMbaGnSPi-pMqwVGw20-UlJUZUZrCMyIXoRxOlohZUnd0vm6cUeP9zcGZEkYf5kMAHCcgMqmrWvRc2miS52jmVKogFlc9cRWF-6vuYGELwqbNjdLIOZnYJuC-gGgmbhKokDIm-b0wPJyf9_A', 'ppinf': '5|1554643214|1555852814|dHJ1c3Q6MToxfGNsaWVudGlkOjQ6MjAxN3x1bmlxbmFtZToyNzolRTYlOUMlQkElRTYlQTIlQjAlRTUlQjglODh8Y3J0OjEwOjE1NTQ2NDMyMTR8cmVmbmljazoyNzolRTYlOUMlQkElRTYlQTIlQjAlRTUlQjglODh8dXNlcmlkOjQ0Om85dDJsdUdQeEx0dk92U1pBVG5xVjNvYk9tOG9Ad2VpeGluLnNvaHUuY29tfA', 'SUV': '0077EACF7B7434015CA9F90AB923A772', 'SUID': '0134747B4631990A000000005CA9F907', 'weixinIndexVisited': '1', 'IPLOC': 'CN1100', 'ABTEST': '8|1554643207|v1'},
             {'ppmdig': '15546432320000005f548f95c22a3584bb8b8d5d21e43308', 'sgid': '14-39976631-AVypibSBPgUZvMiaor5czcuM0', 'pprdig': 'ZAQAppVJb8iW4aLX1isiM9B5OHrOGeQzxtxKjHFneAG4Z7oc0S6Vbp3iOk_qHSaA0PqC5RrRPlKeHrpGT3yfWOFqarTX-RzeMW6kqdSb7XztzHy7_HQvPFLkbtPuenRWxDN2M3n0ed2Rdcj2wGFT3jhBFzdPXSpSVwkhnZ4ZKwE', 'ppinf': '5|1554643232|1555852832|dHJ1c3Q6MToxfGNsaWVudGlkOjQ6MjAxN3x1bmlxbmFtZToxODolRTQlQjglQkUlRTQlQjglQUF8Y3J0OjEwOjE1NTQ2NDMyMzJ8cmVmbmljazoxODolRTQlQjglQkUlRTQlQjglQUF8dXNlcmlkOjQ0Om85dDJsdUtmNjJWLXNDU01rNjJMaFZkS1hoWGNAd2VpeGluLnNvaHUuY29tfA', 'SUV': '00B9EAD57B7434015CA9F91CBA0A7716', 'SUID': '0134747B4631990A000000005CA9F91A', 'weixinIndexVisited': '1', 'IPLOC': 'CN1100', 'ABTEST': '6|1554643226|v1'}]
    pool2 = [{'https': 'http://61.178.149.237:59042'},
             {'https': 'http://163.125.66.161:9797'},
             {'https': 'http://163.125.66.217:9797'},
             {'https': 'http://180.141.90.172:53281'},
             {'https': 'http://124.237.83.14:53281'},
             {'https': 'http://114.119.116.92:61066'},
             {'https': 'http://116.209.58.237:9999'},
             {'https': 'http://110.52.235.170:9999'},
             {'https': 'http://110.52.235.117:9999'}]
    wxspider = spider.WXAccountsSpider(
        keys, pool1, pool2)  # 暂时只使用一个spider
    wxspider.run()
    downloader = AccountsDownloader(pool1, pool2)
    downloader.run()


if __name__ == "__main__":
    key_list = ["女性", "时尚", "女性健康", "星座", "少女", "穿衣", "fashion"]
    main(key_list)
