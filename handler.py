#!/usr/bin/env python3
# -*- coding=utf-8 -*-
import logging
import traceback
import datetime
import jieba
import time

from settings import BasicConfig
from tempfile import NamedTemporaryFile
from subprocess import Popen, PIPE
from library import BaiduVoice, TuringRobot
from utils import init_logger, Keyword, cache, timestamp, generate_response ,getPinyin, mp3_to_wav
from apis import WeatherAPIClient

logger = init_logger()

FUNC_MAP = {
    Keyword(['几点']).value: 'say_time',
    Keyword(['时间', '显示']).value: 'show_time',
    Keyword(['查询', '天气']).value: 'weather_today',
    Keyword(['今天', '天气']).value: 'weather_today',
    Keyword(['明天', '天气']).value: 'weather_tomo',
    Keyword(['打开','客厅', '灯']).value: 'light_kt_open',
    Keyword(['关闭','客厅', '灯']).value: 'light_kt_close'
}

class BaseHandler(object):
    def __init__(self,baidu_token = None):
        if not baidu_token:
            try:
                token = BaiduVoice.get_baidu_token(BasicConfig.VOICE_API_KEY, BasicConfig.VOICE_SECRET)
                self.token = token['access_token']
            except Exception as e:
                logger.warn('======Get baidu voice token failed, %s', traceback.format_exc())
                raise e
        else:
            self.token = baidu_token
        self.bv = BaiduVoice(self.token)

    def __repr__(self):
        return '<BaseHandler>'

    def outputwrite(self,data):
        with open(BasicConfig.OUTPUT_NAME, 'wb') as f:
            f.write(data)

    # @cache
    def feedback(self, content=None):
        if content:
            try:
                self.outputwrite(self.bv.tts(content))
                self.aplay()
            except Exception as e:
                logger.debug('======Baidu TTS failed, %s', traceback.format_exc())

    def aplay(self, file_ = BasicConfig.OUTPUT_NAME,vol = '1', is_buffer=False):
        if is_buffer:
            temp = TemporaryFile()
            temp.write(file_)
            temp.seek(0)
            p = Popen(['aplay', '-D', 'plughw:1,0', '-'], stdin=temp)
            temp.close()
        else:
            #p = Popen(['aplay', '-D', 'plughw:1,0', BasicConfig.OUTPUT_NAME])
            p = Popen(['play', '-v', vol, '-q', file_])
        p.wait()

    def process(self, results):
        seg_list = list(jieba.cut(results, cut_all=True))
        command = Keyword(list(set(x for x in seg_list) & BasicConfig.KEYWORDS))
        func = FUNC_MAP.get(command.value, 'default')
        logger.info("function is %s , data is %s" % (func,results))
        return func,results

    def execute(self, func_name, result):
        func = getattr(ActionHandler, func_name)
        return func(self, result)
 
    def run(self,msg=''):
        try:
            if msg is '':
                # mp3_to_wav()
                results = self.bv.asr(BasicConfig.INPUT_NAME)
                msg = results[0]
            func, result = self.process(msg)
            content = self.execute(func, result)
            self.feedback(content)
            return msg,content
        except Exception as e:
            logger.info(e)
            logger.debug('======run failed, %s', traceback.format_exc())
            return '解析语音失败',str(e)

class ActionHandler(object):
    """docstring for ActionHandler"""

    @staticmethod
    def default(base_handler, result):
        return ''
        robot = TuringRobot(BasicConfig.TURING_KEY)
        try:
            content = robot.ask_turing(result)
        except Exception as e:
            logger.warn(traceback.format_exc())
            return '没有找到问题的答案'
        else:
            return content.decode()

    @staticmethod
    def say_time(base_handler, result):
        return datetime.datetime.now().strftime("现在时刻，%H点%M分")

    @staticmethod
    def show_time(base_handler, result):

        return '显示完毕'

    @staticmethod
    def light_kt_open(base_handler, result):

        return '客厅灯已打开'

    @staticmethod
    def light_kt_close(base_handler, result):

        return '客厅灯已关闭'

    @staticmethod
    def weather_tomo(base_handler, result):
        return ActionHandler.query_weather('tomo')

    @staticmethod
    def weather_today(base_handler, result):
        return ActionHandler.query_weather('today')

    @staticmethod
    def query_weather(today_or_tomo):
        def tempread(temp):
            return temp if int(temp) > 0 else ('负%d' % abs(int(temp)))
        client = WeatherAPIClient()
        try:
            weatherreport = client.weather()
        except Exception as e:
            logger.warn(traceback.format_exc())
            return '查询天气失败，请检查日志'
        if today_or_tomo == 'today':
            TODAY_WEATHER_TEXT = u'今日{city}天气，{weather}，温度{min}到{max}摄氏度，湿度{humidity}，{pop}。'
            text = TODAY_WEATHER_TEXT.format(
                city=weatherreport['city'],
                weather=weatherreport['weather'],
                min=tempread(weatherreport['templow']),
                max=tempread(weatherreport['temphigh']),
                humidity=weatherreport['humidity'],
                pop=weatherreport['aqi']['aqiinfo']['affect']
                )
            # content['daily'][1]:[{"date":"2017-12-22","sunrise":"07:08","week":"星期五","sunset":"16:35","night":{"templow":"-2","img":"0","winddirect":"北风","windpower":"4-5级","weather":"晴"},"day":{"img":"0","winddirect":"西南风","windpower":"5-6级","weather":"晴","temphigh":"8"}},{"date":"2017-12-23","sunrise":"07:09","week":"星期六","sunset":"16:35","night":{"templow":"-2","img":"1","winddirect":"南风","windpower":"4-5级","weather":"多云"},"day":{"img":"1","winddirect":"北风","windpower":"4-5级","weather":"多云","temphigh":"5"}}
        elif today_or_tomo == 'tomo':
            TOMO_WEATHER_TEXT = u'{city}明天白天{weather},{min}到{max}摄氏度，{winddirect}{windpower}。'
            tomo_weather = weatherreport['daily'][1]
            text = TOMO_WEATHER_TEXT.format(
                city=weatherreport['city'],
                weather=tomo_weather['day']['weather'],
                min=tempread(tomo_weather['night']['templow']),
                max=tempread(tomo_weather['day']['temphigh']),
                winddirect=tomo_weather['day']['winddirect'],
                windpower=tomo_weather['day']['windpower']
                )
        else:
            return '查询天气失败，请检查日志'
        return text

