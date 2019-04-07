from bs4 import BeautifulSoup
import requests
import re
import redis

header = {
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8',
    'Accept-Encoding': 'gzip, deflate',
    'Accept-Language': 'zh-CN,zh;q=0.9',
    'Connection': 'keep-alive',
    'Host': 'weixin.sogou.com',
    'Upgrade-Insecure-Requests': '1',
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/62.0.3202.94 Safari/537.36',
}
r = redis.Redis(host="127.0.0.1", port=6379)
obj = r.brpop("urls", timeout=2)
url = obj[1].decode('utf-8')
content = requests.get(url,headers=header).content
bsObj = BeautifulSoup(str(content, encoding="utf-8"), "html.parser")
divs = bsObj.find_all("li",{"id":re.compile("sogou_vr_*")})

for child in divs:
    id = child.find("label", {"name": "em_weixinhao"}).text
    name = child.find("a", {"uigs": re.compile("account_name_*")}).text
    # dds = child.find_all("dd")
    print(id)
    print(name)
    # authname = dds[1].text
    # description = dds[0].text
    # print(authname)
    # print(description)