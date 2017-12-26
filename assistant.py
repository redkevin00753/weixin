#!/usr/bin/env python3
# -*- coding=utf-8 -*-

import time,os
import threading
from weixinClient import *
from myclient import *

from handler import BaseHandler

class MyWXBot(WXBot):
    def __init__(self):
        super().__init__()
        self.bh = BaseHandler()


    def handle_msg_all(self, msg):
        """
        content_type_id:
            0 -> Text
            1 -> Location
            3 -> Image
            4 -> Voice
            5 -> Recommend
            6 -> Animation
            7 -> Share
            8 -> Video
            9 -> VideoCall
            10 -> Redraw
            11 -> Empty
            99 -> Unknown
        """
        words = feedback = ''
        if msg['content']['type'] == 0:
            words,feedback = self.bh.run(msg['content']['data'])
        if msg['content']['type'] == 4:
            print(msg['content']['data'])
            words,feedback = self.bh.run()

        if isinstance(feedback, str):
            self.send_msg("口令:%s,执行结果:%s" % (words,feedback))
        else:
            self.send_msg("get error -> %s" % type(words+'/'+feedback))


#     def schedule(self):
# #        for i in [1,2,3]:
#  #           self.send_msg(u'十八子阳', u'schedule[委屈]%s' % i)
#          #   #time.sleep(1)
#          pass

def main():
    print('weichat')
    wx = MyWXBot()
    wx.DEBUG = True
    wx.run()

if __name__ == '__main__':
    mc = MyClient()
    tmc = threading.Thread(target=mc.loop)
    tmc.setDaemon(True)
    tmc.start()
    print("*******************************************************")
    print("*               PERSONAL ASSISTANTS                   *")
    print("*                       (c) 2017 Kevin (weixin)       *")
    print("*******************************************************")
    try:
        main()
    except KeyboardInterrupt:
        pass
