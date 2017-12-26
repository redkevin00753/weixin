#!/usr/bin/env python3
# -*- coding=utf-8 -*-
"""
Kevin AI library
=====================

"""
__title__ = 'APIs'
__version__ = '0.0.1'
__author__ = 'kevin'

from .api import Wolfram, TuringRobot, BaiduVoice
from .clients import BaseClient
from . import utils
from .exceptions import APIError, RespError, RecognitionError, VerifyError, QuotaError
