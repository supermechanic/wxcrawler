from selenium import webdriver
import time
def get_cookie():  # 获取cookie
    chrome_obj = webdriver.Chrome()
    chrome_obj.get("http://weixin.sogou.com/")

    chrome_obj.find_element_by_xpath('//*[@id="loginBtn"]').click()
    time.sleep(15)
    cookies = chrome_obj.get_cookies()
    cookie = {}
    for items in cookies:
        cookie[items.get('name')] = items.get('value')
    return cookie

def get_n_cookies(n = 1):
    cookie_list = list()
    for i in range(n):
        print(i)
        cookie = get_cookie()
        cookie_list.append(cookie)
    return cookie_list

if __name__ == "__main__":
    cookies=get_n_cookies(2)
    print(cookies)