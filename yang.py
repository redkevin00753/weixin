#!/usr/bin/env python
# coding: utf-8

import time,os
from wechat import *

class MyWXBot(WXBot):
    def handle_msg_all(self, msg):
        #print msg
        #url='http://www.tuling123.com/openapi/api?key=0426cf5db84b7c46091c5390288cf39b&info='
        #r = self.session.get(url+msg['content']['data'])
        #r.encoding = 'utf-8'
        #dic = json.loads(r.text)
        print msg;
        
        #if msg['msg_type_id'] == 4 and msg['content']['type'] == 0:
        #if msg['content']['type'] == 0:
            #reply=raw_input('your reply : ')
        #    if msg['content']['data'][:1]=='@' and msg['content']['data'][:4]!=u'@小管家':
        #        pass
        #    else:
        #        self.send_msg_by_uid(dic['text'], msg['user']['id'])

    def schedule(self):
#        for i in [1,2,3]:
 #           self.send_msg(u'十八子阳', u'schedule[委屈]%s' % i)
         #   #time.sleep(1)
         pass

def main():
    bot = MyWXBot()
    bot.DEBUG = True
    bot.run()

if __name__ == '__main__':
    main()
