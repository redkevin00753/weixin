from handler import BaseHandler
from subprocess import Popen, PIPE, getoutput

bh = BaseHandler()

def mp3_to_wav():
    #sox 123.mp3 -e signed-integer -r 16k file.wav
    v_max = (int(float(getoutput('sox voice.wav -n stat -v')))-1)
    p = Popen(['sox', '-v', str(v_max), 'voice.wav', 'record.wav'])
    p.wait()
    return True

while True:
    input("?")
    mp3_to_wav()
    results = bh.bv.asr('record.wav')
    msg = results[0]
    func, result = bh.process(msg)
    content = bh.execute(func, result)
    bh.feedback(content)
    print(msg)