import time,os
import threading



def func1():
    while True:
        print('func1')
        time.sleep(1)

def func2():
    while True:
        print('func2')
        time.sleep(1)


if __name__ == '__main__':
    tmc = threading.Thread(target=func1)
    tmc.setDaemon(True)
    tmc.start()
    print("*******************************************************")
    print("*               PERSONAL ASSISTANTS                   *")
    print("*                       (c) 2017 Kevin (weixin)       *")
    print("*******************************************************")
    try:
        func2()
    except KeyboardInterrupt:
        pass