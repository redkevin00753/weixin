#!/usr/bin/env python3
# -*- coding=utf-8 -*-

import os
import sys
import webbrowser
import pyqrcode
import requests
import json
import xml.dom.minidom
import urllib
import time
import re
import random
import html
from requests.exceptions import ConnectionError, ReadTimeout


UNKONWN = 'unkonwn'
SUCCESS = '200'
SCANED  = '201'
TIMEOUT = '408'

def show_image(file):
    """
    跨平台显示图片文件
    :param file: 图片文件路径
    """
    if sys.version_info >= (3, 3):
        from shlex import quote
    else:
        from pipes import quote

    if sys.platform == "darwin":
        command = "open -a /Applications/Preview.app %s&" % quote(file)
        os.system(command)
    else:
        webbrowser.open(file)

class WXBot:
    """WXBot功能类"""
    def __init__(self):
        self.DEBUG = True
        self.uuid = ''
        self.base_uri = ''
        self.redirect_uri = ''
        self.uin = ''
        self.sid = ''
        self.skey = ''
        self.pass_ticket = ''
        self.device_id = 'e' + repr(random.random())[2:17]
        self.base_request = {}
        self.sync_key_str = ''
        self.sync_key = []
        self.sync_host = ''

        self.session = requests.Session()
        self.session.headers.update({'User-Agent': 'Mozilla/5.0 (X11; Linux i686; U;) Gecko/20070322 Kazehakase/0.4.5'})
        self.conf = {'qr': 'png'}

        self.my_account = {}  # 当前账户

        # 所有相关账号: 联系人, 公众号, 群组, 特殊账号
        self.member_list = []

        # Lord info
        self.lord_name = 'mylord'
        self.lord_uid = ''

        self.codeset = set()

    def do_request(self, url):
        r = self.session.get(url)
        r.encoding = 'utf-8'
        data = r.text
        param = re.search(r'window.code=(\d+);', data)
        code = param.group(1)
        return code, data

    def test_sync_check(self):
        for host in ['webpush', 'webpush2']:
            self.sync_host = host
            retcode = self.sync_check()[0]
            if retcode == '0':
                return True
        return False

    def sync_check(self):
        params = {
            'r': int(time.time()),
            'sid': self.sid,
            'uin': self.uin,
            'skey': self.skey,
            'deviceid': self.device_id,
            'synckey': self.sync_key_str,
            '_': int(time.time()),
        }
        url = 'https://' + self.sync_host + '.wx.qq.com/cgi-bin/mmwebwx-bin/synccheck?' + urllib.parse.urlencode(params)
        try:
            r = self.session.get(url, timeout=60)
        except (ConnectionError, ReadTimeout):
            return [-1, -1]
        r.encoding = 'utf-8'
        data = r.text
        pm = re.search(r'window.synccheck=\{retcode:"(\d+)",selector:"(\d+)"\}', data)
        retcode = pm.group(1)
        selector = pm.group(2)
        return [retcode, selector]

    def sync(self):
        url = self.base_uri + '/webwxsync?sid=%s&skey=%s&lang=en_US&pass_ticket=%s' \
                              % (self.sid, self.skey, self.pass_ticket)
        params = {
            'BaseRequest': self.base_request,
            'SyncKey': self.sync_key,
            'rr': ~int(time.time())
        }
        try:
            r = self.session.post(url, data=json.dumps(params), timeout=60)
        except (ConnectionError, ReadTimeout):
            return None
        r.encoding = 'utf-8'
        dic = json.loads(r.text)
        if dic['BaseResponse']['Ret'] == 0:
            self.sync_key = dic['SyncKey']
            self.sync_key_str = '|'.join([str(keyVal['Key']) + '_' + str(keyVal['Val'])
                                          for keyVal in self.sync_key['List']])
        return dic

    def get_uuid(self):
        url = 'https://login.weixin.qq.com/jslogin'
        params = {
            'appid': 'wx782c26e4c19acffb',
            'fun': 'new',
            'lang': 'zh_CN',
            '_': int(time.time()) * 1000 + random.randint(1, 999),
        }
        r = self.session.get(url, params=params)
        r.encoding = 'utf-8'
        data = r.text
        regx = r'window.QRLogin.code = (\d+); window.QRLogin.uuid = "(\S+?)"'
        pm = re.search(regx, data)
        if pm:
            code = pm.group(1)
            self.uuid = pm.group(2)
            return code == '200'
        return False

    def gen_qr_code(self, qr_file_path):
        string = 'https://login.weixin.qq.com/l/' + self.uuid
        print(string)
        qr = pyqrcode.create(string)
        if self.conf['qr'] == 'png':
            qr.png(qr_file_path, scale=8)
            show_image(qr_file_path)
            # img = Image.open(qr_file_path)
            # img.show()
        elif self.conf['qr'] == 'tty':
            print(qr.terminal(quiet_zone=1))

    def wait4login(self):
        """
        http comet:
        tip=1, 等待用户扫描二维码,
               201: scaned
               408: timeout
        tip=0, 等待用户确认登录,
               200: confirmed
        """
        LOGIN_TEMPLATE = 'https://login.weixin.qq.com/cgi-bin/mmwebwx-bin/login?tip=%s&uuid=%s&_=%s'
        tip = 1

        try_later_secs = 1
        MAX_RETRY_TIMES = 10

        code = UNKONWN

        retry_time = MAX_RETRY_TIMES
        while retry_time > 0:
            url = LOGIN_TEMPLATE % (tip, self.uuid, int(time.time()))
            code, data = self.do_request(url)
            if code == SCANED:
                print('[INFO] Please confirm to login .')
                tip = 0
            elif code == SUCCESS:  # 确认登录成功
                param = re.search(r'window.redirect_uri="(\S+?)";', data)
                redirect_uri = param.group(1) + '&fun=new'
                # print(redirect_uri)
                self.redirect_uri = redirect_uri
                self.base_uri = redirect_uri[:redirect_uri.rfind('/')]
                # print(self.base_uri)
                return code
            elif code == TIMEOUT:
                print('[ERROR] WeChat login timeout. retry in %s secs later...'% try_later_secs)

                tip = 1 # 重置
                retry_time -= 1
                time.sleep(try_later_secs)
            else:
                print('[ERROR] WeChat login exception return_code=%s. retry in %s secs later...' % (code, try_later_secs))
                tip = 1
                retry_time -= 1
                time.sleep(try_later_secs)

        return code

    def login(self):
        if len(self.redirect_uri) < 4:
            print('[ERROR] Login failed due to network problem, please try again.')
            return False
        r = self.session.get(self.redirect_uri)
        r.encoding = 'utf-8'
        data = r.text
        # print(data)
        doc = xml.dom.minidom.parseString(data)
        root = doc.documentElement

        for node in root.childNodes:
            if node.nodeName == 'skey':
                self.skey = node.childNodes[0].data
            elif node.nodeName == 'wxsid':
                self.sid = node.childNodes[0].data
            elif node.nodeName == 'wxuin':
                self.uin = node.childNodes[0].data
            elif node.nodeName == 'pass_ticket':
                self.pass_ticket = node.childNodes[0].data

        if '' in (self.skey, self.sid, self.uin, self.pass_ticket):
            return False

        self.base_request = {
            'Uin': self.uin,
            'Sid': self.sid,
            'Skey': self.skey,
            'DeviceID': self.device_id,
        }
        return True

    def init(self):
        url = self.base_uri + '/webwxinit?r=%i&lang=en_US&pass_ticket=%s' % (int(time.time()), self.pass_ticket)
        params = {
            'BaseRequest': self.base_request
        }
        r = self.session.post(url, data=json.dumps(params))
        r.encoding = 'utf-8'
        dic = json.loads(r.text)
        self.sync_key = dic['SyncKey']
        self.my_account = dic['User']
        self.sync_key_str = '|'.join([str(keyVal['Key']) + '_' + str(keyVal['Val'])
                                      for keyVal in self.sync_key['List']])
        # print(self.sync_key)
        # print(self.my_account)
        # print(self.sync_key_str)
        return dic['BaseResponse']['Ret'] == 0

    def status_notify(self):
        url = self.base_uri + '/webwxstatusnotify?lang=zh_CN&pass_ticket=%s' % self.pass_ticket
        self.base_request['Uin'] = int(self.base_request['Uin'])
        params = {
            'BaseRequest': self.base_request,
            "Code": 3,
            "FromUserName": self.my_account['UserName'],
            "ToUserName": self.my_account['UserName'],
            "ClientMsgId": int(time.time())
        }
        r = self.session.post(url, data=json.dumps(params))
        r.encoding = 'utf-8'
        dic = json.loads(r.text)
        return dic['BaseResponse']['Ret'] == 0

    def get_lord(self):
        """获取当前账户的所有相关账号(包括联系人、公众号、群聊、特殊账号)"""
        url = self.base_uri + '/webwxgetcontact?pass_ticket=%s&skey=%s&r=%s' \
                              % (self.pass_ticket, self.skey, int(time.time()))
                 
        r = self.session.post(url, data='{}')
        r.encoding = 'utf-8'
        # if self.DEBUG:
        #     with open('contacts.json', 'w') as f:
        #         f.write(r.text)
        dic = json.loads(r.text)
        self.member_list = dic['MemberList']

        for contact in self.member_list:
            if contact['RemarkName'] == self.lord_name:
                self.lord_uid = contact['UserName']
            else:
                pass
        # if self.DEBUG:
        #     with open('member_list.json', 'w') as f:
        #         f.write(json.dumps(self.member_list))
        return True

    def proc_msg(self):
        self.test_sync_check()
        while True:
            check_time = time.time()
            [retcode, selector] = self.sync_check()
            if retcode == '1100':  # 从微信客户端上登出
                break
            elif retcode == '1101':  # 从其它设备上登了网页微信
                break
            elif retcode == '0':
                if selector == '2':  # 有新消息
                    r = self.sync()
                    if r is not None:
                        self.handle_msg(r)
                elif selector == '7':  # 在手机上操作了微信
                    r = self.sync()
                    if r is not None:
                        self.handle_msg(r)
                elif selector == '0':  # 无事件
                    pass
                else:                  # not sure 
                    self.codeset.add(selector)
                    print(self.codeset)
                    r = self.sync()
                    if r is not None:
                        self.handle_msg(r)
            else:
                print('retcode is %s ,selector is %s' % (retcode,selector))
            #self.schedule()
            check_time = time.time() - check_time
            if check_time < 0.8:
                time.sleep(1 - check_time)

    def run(self):
        self.get_uuid()
        self.gen_qr_code('qr.png')
        print('[INFO] Please use WeChat to scan the QR code .')

        result = self.wait4login()
        if result != SUCCESS:
            print('[ERROR] Web WeChat login failed. failed code=%s' % result)
            return

        if self.login():
            print('[INFO] Web WeChat login succeed .')
        else:
            print('[ERROR] Web WeChat login failed .')
            return

        if self.init():
            print('[INFO] Web WeChat init succeed .')
        else:
            print('[INFO] Web WeChat init failed')
            return
        self.status_notify()
        self.get_lord()
        print('[INFO] Get %d contacts' % len(self.member_list))
        print('[INFO] Start to process messages .')
        # print('get lord uid %s ' % self.lord_uid )
        self.proc_msg()

    def handle_msg(self, r):
        """
        处理原始微信消息的内部函数
        msg_type_id:
            0 -> Init
            1 -> Self
            2 -> FileHelper
            3 -> Group
            4 -> Contact
            5 -> Public
            6 -> Special
            99 -> Unknown
        :param r: 原始微信消息
        """
        for msg in r['AddMsgList']:
            msg_type_id = 99
            user = {'id': msg['FromUserName'], 'name': 'unknown'}
            if msg['MsgType'] == 51:  # init message
                msg_type_id = 0
                user['name'] = 'system'
            elif msg['FromUserName'] == self.my_account['UserName']:  # Self
                msg_type_id = 1
                user['name'] = 'self'
            elif msg['ToUserName'] == 'filehelper':  # File Helper
                msg_type_id = 2
                user['name'] = 'file_helper'
            elif msg['FromUserName'][:2] == '@@':  # Group
                msg_type_id = 3
                user['name'] = 'Group'
            elif msg['FromUserName'] == self.lord_uid:  # Contact
                msg_type_id = 4
                user['name'] = 'lord'
            else:
                msg_type_id = 99
                user['name'] = 'unknown'
            if not user['name']:
                user['name'] = 'unknown'
            user['name'] = html.unescape(user['name'])

            if self.DEBUG and msg_type_id != 0:
                print('[MSG_FROM] %s:' % user['name'])
            content = self.extract_msg_content(msg_type_id, msg)
            message = {'msg_type_id': msg_type_id,
                       'msg_id': msg['MsgId'],
                       'content': content,
                       'to_user_id': msg['ToUserName'],
                       'user': user}
            self.handle_msg_all(message)

    def extract_msg_content(self, msg_type_id, msg):
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
            :param msg_type_id: 消息类型id
            :param msg: 消息结构体
            :return: 解析的消息
            """
            mtype = msg['MsgType']
            content = html.unescape(msg['Content'])
            msg_id = msg['MsgId']

            msg_content = {}
            if msg_type_id not in [1,4]:
                return {'type': mtype, 'data': ' not need process message !'}
            if mtype == 1:
                if content.find('http://weixin.qq.com/cgi-bin/redirectforward?args=') != -1:
                    r = self.session.get(content)
                    r.encoding = 'gbk'
                    data = r.text
                    pos = self.search_content('title', data, 'xml')
                    msg_content['type'] = 1
                    msg_content['data'] = pos
                    msg_content['detail'] = data
                    if self.DEBUG:
                        print('    [Location] %s ' %  pos)
                else:
                    msg_content['type'] = 0
                    msg_content['data'] = content
                    if self.DEBUG:
                        try:
                            print('    [Text] %s' % msg_content['data'])
                        except UnicodeEncodeError:
                            print('    [Text] (illegal text).')

            elif mtype == 3:
                msg_content['type'] = 3
                msg_content['data'] = self.get_msg_img_url(msg_id)
                if self.DEBUG:
                    image = self.get_msg_img(msg_id)
                    print('    [Image] %s' % image)
            elif mtype == 34:
                msg_content['type'] = 4
                msg_content['data'] = self.get_voice_url(msg_id)
                if self.DEBUG:
                    voice = self.get_voice(msg_id)
                    print('    [Voice] %s' %  voice)
            elif mtype == 42:
                msg_content['type'] = 5
                info = msg['RecommendInfo']
                msg_content['data'] = {'nickname': info['NickName'],
                                       'alias': info['Alias'],
                                       'province': info['Province'],
                                       'city': info['City'],
                                       'gender': ['unknown', 'male', 'female'][info['Sex']]}
                if self.DEBUG:
                    print('    [Recommend]')
                    print('    -----------------------------')
                    print('    | NickName: %s' % info['NickName'])
                    print('    | Alias: %s' % info['Alias'])
                    print('    | Local: %s %s' % (info['Province'], info['City']))
                    print('    | Gender: %s' % ['unknown', 'male', 'female'][info['Sex']])
                    print('    -----------------------------')
            elif mtype == 47:
                msg_content['type'] = 6
                msg_content['data'] = self.search_content('cdnurl', content)
                if self.DEBUG:
                    print('    [Animation] %s' % msg_content['data'])
            elif mtype == 49:
                msg_content['type'] = 7
                app_msg_type = ''
                if msg['AppMsgType'] == 3:
                    app_msg_type = 'music'
                elif msg['AppMsgType'] == 5:
                    app_msg_type = 'link'
                elif msg['AppMsgType'] == 7:
                    app_msg_type = 'weibo'
                else:
                    app_msg_type = 'unknown'
                msg_content['data'] = {'type': app_msg_type,
                                       'title': msg['FileName'],
                                       'desc': self.search_content('des', content, 'xml'),
                                       'url': msg['Url'],
                                       'from': self.search_content('appname', content, 'xml')}
                if self.DEBUG:
                    print('    [Share] %s' % app_msg_type)
                    print('    --------------------------')
                    print('    | title: %s' % msg['FileName'])
                    print('    | desc: %s' % self.search_content('des', content, 'xml'))
                    print('    | link: %s' % msg['Url'])
                    print('    | from: %s' % self.search_content('appname', content, 'xml'))
                    print('    --------------------------')

            elif mtype == 62:
                msg_content['type'] = 8
                msg_content['data'] = content
                if self.DEBUG:
                    print('    [Video] Please check on mobiles')
            elif mtype == 53:
                msg_content['type'] = 9
                msg_content['data'] = content
                if self.DEBUG:
                    print('    [Video Call]')
            elif mtype == 10002:
                msg_content['type'] = 10
                msg_content['data'] = content
                if self.DEBUG:
                    print('    [Redraw]')
            elif mtype == 10000:  # unknown, maybe red packet, or group invite
                msg_content['type'] = 12
                msg_content['data'] = msg['Content']
                if self.DEBUG:
                    print('    [Unknown]')
            else:
                msg_content['type'] = 99
                msg_content['data'] = content
                if self.DEBUG:
                    print('    [Unknown]')
            return msg_content

    def handle_msg_all(self, msg):
        """
        处理所有消息，请子类化后覆盖此函数
        msg:
            msg_id  ->  消息id
            msg_type_id  ->  消息类型id
            user  ->  发送消息的账号id
            content  ->  消息内容
        :param msg: 收到的消息
        """
        pass 
    def schedule(self):
        """
        做任务型事情的函数，如果需要，可以在子类中覆盖此函数
        此函数在处理消息的间隙被调用，请不要长时间阻塞此函数
        """
        pass

    def send_msg_by_uid(self, word, dst='filehelper'):
        url = self.base_uri + '/webwxsendmsg?pass_ticket=%s' % self.pass_ticket
        msg_id = str(int(time.time() * 1000)) + str(random.random())[:5].replace('.', '')
        params = {
            'BaseRequest': self.base_request,
            'Msg': {
                "Type": 1,
                "Content": word,
                "FromUserName": self.my_account['UserName'],
                "ToUserName": dst,
                "LocalID": msg_id,
                "ClientMsgId": msg_id
            }
        }
        headers = {'content-type': 'application/json; charset=UTF-8'}
        data = json.dumps(params, ensure_ascii=False).encode('utf8')
        try:
            r = self.session.post(url, data=data, headers=headers)
        except (ConnectionError, ReadTimeout):
            return False
        dic = r.json()
        return dic['BaseResponse']['Ret'] == 0

    def send_msg(self, word, isfile=False):
        uid = self.lord_uid
        if uid is not '':
            if self.send_msg_by_uid(word, uid):
                return True
            else:
                return False
        else:
            if self.DEBUG:
                print('[ERROR] Lord id not found .')
            return True


    @staticmethod
    def search_content(key, content, fmat='attr'):
        if fmat == 'attr':
            pm = re.search(key + '\s?=\s?"([^"<]+)"', content)
            if pm:
                return pm.group(1)
        elif fmat == 'xml':
            pm = re.search('<{0}>([^<]+)</{0}>'.format(key), content)
            if pm:
                return pm.group(1)
        return 'unknown'     

    @staticmethod
    def to_unicode(string, encoding='utf-8'):
        """
        将字符串转换为Unicode
        :param string: 待转换字符串
        :param encoding: 字符串解码方式
        :return: 转换后的Unicode字符串
        """
        if isinstance(string, str):
            return string.decode(encoding)
        elif isinstance(string, unicode):
            return string
        else:
            raise Exception('Unknown Type')  

    def get_msg_img_url(self, msgid):
        return self.base_uri + '/webwxgetmsgimg?MsgID=%s&skey=%s' % (msgid, self.skey)

    def get_msg_img(self, msgid):
        """
        获取图片消息，下载图片到本地
        :param msgid: 消息id
        :return: 保存的本地图片文件路径
        """
        url = self.base_uri + '/webwxgetmsgimg?MsgID=%s&skey=%s' % (msgid, self.skey)
        r = self.session.get(url)
        data = r.content
        fn = 'images/img_' + msgid + '.jpg'
        with open(fn, 'wb') as f:
            f.write(data)
        return fn

    def get_voice_url(self, msgid):
        return self.base_uri + '/webwxgetvoice?msgid=%s&skey=%s' % (msgid, self.skey)

    def get_voice(self, msgid):
        """
        获取语音消息，下载语音到本地
        :param msgid: 语音消息id
        :return: 保存的本地语音文件路径
        """
        url = self.base_uri + '/webwxgetvoice?msgid=%s&skey=%s' % (msgid, self.skey)
        r = self.session.get(url)
        data = r.content
        fn = 'voice.mp3'
        with open(fn, 'wb') as f:
            f.write(data)
        return fn
