#!/usr/bin/env python3
# -*- coding=utf-8 -*-
import logging
from library import APIError, RespError, RecognitionError, VerifyError, QuotaError


class LogConfig(object):
    LOGGING_LOCATION = './log/assistant.log'
    LOGGING_LOG_FORMAT = '%(asctime)s %(funcName)s:%(lineno)d [%(levelname)s] %(message)s'
    LOGGING_CONSOLE_FORMAT = '%(name)-6s: %(message)s'
    LOGGING_LOG_LEVEL = logging.DEBUG
    LOGGING_CONSOLE_LEVEL = logging.INFO

class RedisConfig(object):
    """docstring for RedisConfig"""
    HOST_ADDR = 'localhost'
    PORT = 6379
    DB = 0
    SOCKET_TIMEOUT = 1


class BasicConfig(object):
    """Basic config for the raspi_assistant."""
    # Your location, only used in weather queries
    PERSONA = '傻子'
    LOCATION = '大连'
    TURING_KEY = '0426cf5db84b7c46091c5390288cf39b'
    VOICE_API_KEY = 'YVNd3SRFPwETI4f17PuLgm4d'
    VOICE_SECRET = 'fe8a25d3ae5aab3fd8ce54443b63ee36'
    KEYWORDS = {'今天', '明天', '天气', '打开', '关闭', '客厅', '灯', '几点' , '时间', '显示'}
    VOICE_NAME = 'voice.mp3'
    INPUT_NAME = 'record.wav'
    OUTPUT_NAME = 'output.mp3'
    RESPONSES = {
        1: '您说',
        # 2: '爹，我来了',
        # 3: '听着呢爹滴',
        # 4: '父亲大人请说',
        # 5: '请说', 
        # 6: '干什么啊，爹',
        # 7: '父亲大人，我来了',
        # 8: '我才不叫爹,有事说事' 
    }
    BAD_RESPONSES = {
        1: '别闹人',
        2: '没有声音啊',
        3: '别烦我', 
        4: '逗我呢啊',
        5: '原谅我没听到'
    }


class GPIOConfig(object):
    """GPIO config"""
    VOICE_SENSOR = 4

# https://way.jd.com/jisuapi/weather?city=%E5%A4%A7%E8%BF%9E&appkey=
class WeatherAPIConfig(object):
    """Baidu API Store is used for weather."""
    API_KEY = 'b7e7629e7695327c3bbe32e4a4e7a7f2'
    WEATHER_URL = 'https://way.jd.com/jisuapi/weather'

class ErrNo(object):
    ExceptionMap = {
        3001: QuotaError,
        3002: VerifyError,
        3003: APIError,
    }
