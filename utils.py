#!/usr/bin/env python3
# -*- coding=utf-8 -*-

import logging
import time
import random
import base64
import redis
import pyaudio
import wave

from functools import wraps
from hashlib import md5
from subprocess import Popen, PIPE, getoutput
from tempfile import TemporaryFile
from logging.handlers import TimedRotatingFileHandler
from settings import LogConfig, RedisConfig, BasicConfig, ErrNo
from library import BaseClient, APIError

conn_pool = redis.ConnectionPool(host=RedisConfig.HOST_ADDR, port=RedisConfig.PORT, db=RedisConfig.DB)

def init_logger():
    handler = TimedRotatingFileHandler(LogConfig.LOGGING_LOCATION, when='MIDNIGHT')
    handler.setFormatter(logging.Formatter(LogConfig.LOGGING_LOG_FORMAT))
    handler.setLevel(LogConfig.LOGGING_LOG_LEVEL)
    console = logging.StreamHandler()
    console.setFormatter(logging.Formatter(LogConfig.LOGGING_CONSOLE_FORMAT))
    console.setLevel(LogConfig.LOGGING_CONSOLE_LEVEL)
    logger = logging.getLogger()
    logger.setLevel(0)
    logger.addHandler(console)
    logger.addHandler(handler)
    return logger

def mp3_to_wav():
    #sox 123.mp3 -e signed-integer -r 16k file.wav
    v_max = (int(float(getoutput('sox voice.mp3 -n stat -v')))-1)
    p = Popen(['sox', '-v', str(v_max), BasicConfig.VOICE_NAME, BasicConfig.INPUT_NAME])
    p.wait()
    return True

def generate_response(flag_="good"):
    """Generate response"""
    if "good" == flag_:
        return BasicConfig.RESPONSES[random.randint(1, len(BasicConfig.RESPONSES))]
    else:
        return BasicConfig.BAD_RESPONSES[random.randint(1, len(BasicConfig.BAD_RESPONSES))]

def unique_id(func, args, kwargs):
    return md5(func.__name__ + repr(args) + repr(kwargs)).hexdigest()


def timestamp():
    return int(time.time() * 1000)


def cache(func):
    """Wrapper for cache the audio"""
    @wraps(func)
    def _(*args, **kwargs):
        cache_handler = CacheHandler()
        id_ = unique_id(func, *args, **kwargs)
        cache = cache_handler.get(id_)
        if cache:
            audio_handler = AudioHandler()
            audio_handler.aplay(base64.b64decode(cache), is_buffer=True)
            # return cache
        else:
            func(*args, **kwargs)
            with open('output.wav', 'rb') as f:
                encoded_audio = base64.b64encode(f.read())
                cache_handler.set(id_, encoded_audio, 86400*7)
            # return buffer_
    return _

class Keyword(object):
    """Object for """
    def __init__(self, list_):
        list_.sort()
        self.keywords = list_
        self.value = '/'.join(list_)

    def __repr__(self):
        return self.value

def single_get_first(unicode1):
    str1 = unicode1.encode('gbk')
    try:
        ord(str1)
        return str1
    except:
        asc = str1[0] * 256 + str1[1] - 65536
        if asc >= -20319 and asc <= -20284:
            return 'a'
        if asc >= -20283 and asc <= -19776:
            return 'b'
        if asc >= -19775 and asc <= -19219:
            return 'c'
        if asc >= -19218 and asc <= -18711:
            return 'd'
        if asc >= -18710 and asc <= -18527:
            return 'e'
        if asc >= -18526 and asc <= -18240:
            return 'f'
        if asc >= -18239 and asc <= -17923:
            return 'g'
        if asc >= -17922 and asc <= -17418:
            return 'h'
        if asc >= -17417 and asc <= -16475:
            return 'j'
        if asc >= -16474 and asc <= -16213:
            return 'k'
        if asc >= -16212 and asc <= -15641:
            return 'l'
        if asc >= -15640 and asc <= -15166:
            return 'm'
        if asc >= -15165 and asc <= -14923:
            return 'n'
        if asc >= -14922 and asc <= -14915:
            return 'o'
        if asc >= -14914 and asc <= -14631:
            return 'p'
        if asc >= -14630 and asc <= -14150:
            return 'q'
        if asc >= -14149 and asc <= -14091:
            return 'r'
        if asc >= -14090 and asc <= -13119:
            return 's'
        if asc >= -13118 and asc <= -12839:
            return 't'
        if asc >= -12838 and asc <= -12557:
            return 'w'
        if asc >= -12556 and asc <= -11848:
            return 'x'
        if asc >= -11847 and asc <= -11056:
            return 'y'
        if asc >= -11055 and asc <= -10247:
            return 'z'
        return ''
     
def getPinyin(string):
    if string==None:
        return None
    lst = list(string)
    charLst = []
    for l in lst:
        charLst.append(single_get_first(l))
    return  ''.join(charLst)

class CacheHandler(object):
    """CacheHandler for manipulating redis."""
    def __init__(self):
        self.client = redis.StrictRedis(
            connection_pool=conn_pool, socket_timeout=RedisConfig.SOCKET_TIMEOUT)

    def set(self, name, value, ttl=None):
        if ttl:
            self.client.setex(name, ttl, value)
        else:
            self.client.set(name, value)

    def get(self, name):
        return self.client.get(name)

    def delete(self, name):
        return self.client.delete(name)

    def expire(self, name, ttl):
        return self.client.expire(name, ttl)

    def zset(self, name, key, score, ttl=None, is_audio=True):
        """zset for audio. if is_audio=True, """
        if is_audio:
            key = base64.b64encode(key)
        if ttl:
            pipeline = self.client.pipeline()
            pipeline.zadd(name, score, key)
            pipeline.expire(name, ttl)
            return pipeline.execute()
        else:
            self.client.zadd(name, score, key)

    def zget(self, name, start, end, is_audio=True):
        ret = self.client.zrange(name, start, end)
        if is_audio:
            return [base64.b64decode(x) for x in ret]
        else:
            return ret

    def zdel(self, name, start, end):
        # zremrangebyrank
        return self.client.zremrangebyrank(name, start, end)



