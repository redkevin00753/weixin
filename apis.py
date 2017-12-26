#!/usr/bin/env python3
# -*- coding=utf-8 -*-

from settings import BasicConfig
from library import BaseClient, APIError
from settings import WeatherAPIConfig

class WeatherAPIClient(BaseClient):
    """Client for handling the process of Baidu APIStore requests."""
    def __init__(self, **kwargs):
        super(WeatherAPIClient, self).__init__(**kwargs)
        self.url = WeatherAPIConfig.WEATHER_URL
        self.params = {'city': BasicConfig.LOCATION,'appkey': WeatherAPIConfig.API_KEY}

    def weather(self):
        try:
            resp = self.get_request(
                url = self.url,
                params = self.params
                )
            content = resp.json()
        except Exception as e:
            raise e
        weather_info = content['result']['result']
        if content['code'] != '10000':
            raise APIError('query weather api failed.')
        return weather_info
