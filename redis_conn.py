# -*- coding: UTF-8 -*-
import redis

#todo, 修改为redis连接池


def newRedisConn(host="127.0.0.1", port=6379):
    return redis.Redis(host=host, port=port)


def getRedisConn():
    return newRedisConn()
