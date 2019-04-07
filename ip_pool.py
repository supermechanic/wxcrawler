import requests
from lxml import etree
import time
import multiprocessing
from multiprocessing import Queue, Pool


def get_all_proxy(queue):

    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 6.1; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/68.0.3440.106 Safari/537.36',
    }
    url = "http://www.xicidaili.com/wn"
    response = requests.get(url, headers=headers)

    # 找到我们需要的ip和post
    html_ele = etree.HTML(response.text)

    ip_eles = html_ele.xpath('//table[@id="ip_list"]/tr/td[2]/text()')
    port_ele = html_ele.xpath('//table[@id="ip_list"]/tr/td[3]/text()')

    # print(len(ip_eles))
    # print(len(port_ele))
    # proxy_list = []
    # 循环所有的代理ip
    for i in range(0, len(ip_eles)):
        # 组装成我们需要的格式
        proxy_str = 'http://' + ip_eles[i] + ':' + port_ele[i]
        # proxy_list.append(proxy_str)
        # 放到我们消息队列
        queue.put(proxy_str)
        # print(proxy_str)

# 检测代理是否可用


def check_all_proxy(proxy):
    # 用百度来检验
    url = 'http://www.baidu.com/s?wd=ip'
    proxy_dict = {
        'http': proxy
    }

    try:
        response = requests.get(url, proxies=proxy_dict, timeout=5)
        # 返回码是200 说明可用
        if response.status_code == 200:
            print('这个人头送的好' + proxy)
            print(proxy)
            return proxy
        else:
            # 这个虽然不是200，但是有返回值说不定能用
            print('这个人头没送好')
            print(proxy)
            return proxy
    except:
        print('这个人头耶耶耶没送好--------------->')


def get_proxy_list():
    # 实例化一个消息队列
    q = Queue()
    # 这个进程用来获取我们需要的proxy
    p = multiprocessing.Process(target=get_all_proxy, args=(q,))
    # proxy_list = get_all_proxy()
    # 开启进程
    p.start()
    # 定义一个进程池，10代表同时开启10个进程
    pool = Pool(10)
    proxy_lists = []
    while True:
        try:
            # 从消息队列获取proxy
            proxy_str = q.get(timeout=5)
        except:
            # 没有就结束死循环
            break
        # 这个进程池里面用来检验proxy是否可用
        res_proxy = pool.apply_async(check_all_proxy, (proxy_str,))
        # print(res_proxy)
        # 把可用的放入到一个列表，但是得循环遍历并且用get()方法获取
        proxy_lists.append(res_proxy)

    res_true_proxy = []
    # 获取所有能用的proxy
    for proxy in proxy_lists:
        res = proxy.get()
        if res:
            res_true_proxy.append(res)
    pool.close()
    pool.join()
    p.join()
    print(res_true_proxy)
    return res_true_proxy

if __name__ == '__main__':
    # 定义一个开始时间
    start_time = time.time()
    get_proxy_list()
    end_time = time.time()
    print('--'*30)
    print('耗时:' + str(end_time-start_time))
