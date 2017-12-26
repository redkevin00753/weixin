#!/usr/bin/env python3
# -*- coding=utf-8 -*-
import audioop
import pyaudio
import wave
import time
import sys


from handler import BaseHandler,logger
from settings import BasicConfig
from utils import generate_response

base_handler = BaseHandler()
lastNscores = [x for x in range(15)]
lastNframes = [x for x in range(100)]
framecounts = 0

class MyClient:
    # # save wav from local input device
    # def recordmicwav(self,file_ = BasicConfig.WAKEUP_NAME,maxsecs=6):
    #     print("record %s" % file_)
    #     secs_save = 2
    #     wf = wave.open(file_, 'wb')
    #     wf.setnchannels(1)
    #     wf.setsampwidth(pyaudio.get_sample_size(pyaudio.paInt16))
    #     wf.setframerate(16000)
    #     time.sleep(secs_save)
    #     last_avgscore = avgscore = sum(lastNscores)/len(lastNscores)
    #     while avgscore > (last_avgscore * 0.4) and (file_ != BasicConfig.WAKEUP_NAME):
    #         avgscore = sum(lastNscores)/len(lastNscores)
    #         # print("last_avgscore = %s avgscore = %s" % (last_avgscore,avgscore))
    #         time.sleep(0.2)
    #         secs_save += 0.2
    #         if secs_save > maxsecs:
    #             break
    #     wf.writeframes(b''.join(lastNframes[-int(secs_save*15):]))
    #     wf.close()
    #     print("done")

    #  analogize voice 1 second check if detected
    def detected(self):
        global framecounts
        magicNo = 40
        framecounts = 0 
        while framecounts != magicNo:
            pass
        framecounts = 0
        list_ = lastNframes[-magicNo:]
        maxlist = [ x for x in range(magicNo)]

        maxlist = [audioop.rms(frame, 2) for frame in list_ ]
        avgvalue = sum(maxlist)/len(maxlist)
        resultlist = [result for result in maxlist if result > avgvalue * 1.5 ] 
        if sum(resultlist)/avgvalue > 19 and len(resultlist)>5:
            # wf = wave.open(BasicConfig.WAKEUP_NAME, 'wb')
            wf = wave.open(BasicConfig.INPUT_NAME, 'wb')
            wf.setnchannels(1)
            wf.setsampwidth(pyaudio.get_sample_size(pyaudio.paInt16))
            wf.setframerate(16000)
            wf.writeframes(b''.join(list_))
            wf.close()
            return True
        else:
            return False

    def callback(self,in_data, frame_count, time_info, status):
        global framecounts
        framecounts += 1
        lastNscores.pop(0)
        lastNframes.pop(0)
        lastNscores.append(audioop.rms(in_data, 2))
        lastNframes.append(in_data)    
        return(in_data, pyaudio.paContinue)

    def loop(self):
        pa = pyaudio.PyAudio()
        stream = pa.open(
            rate=16000,
            channels=1,
            format=pyaudio.paInt16,
            input=True,
            frames_per_buffer=1024,
            stream_callback=self.callback
            )
        for i in range(101):
            time.sleep(0.02)
            print('\rloading %d %% ...' % i , end='')
            sys.stdout.flush()
        print('-- complete --')
        while stream.is_active():
            if self.detected():
                print('detected')
                base_handler.run()
                # base_handler.aplay(BasicConfig.INPUT_NAME,'6')
                # if base_handler.iscall():
                #     base_handler.feedback(generate_response())
                #     recordmicwav(BasicConfig.INPUT_NAME)
                #     base_handler.run()
                # print('wait for next')
        # stop stream (6)
        stream.stop_stream()
        stream.close()
        # close PyAudio (7)
        pa.terminate()