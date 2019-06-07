# -*- coding: utf-8 -*-
"""
test keyboard
"""

#%%
from stg4x.control.keyboard import Keyboard
from threading import Thread
def test_key():    
    def test(key='-'):
        import time
        for i in range(0,10):    
            time.sleep(1)
            Keyboard.press_release(key)        
    t = Thread(target=test)
    t.start()
    t.join()
    
def test_type():
    def test(word=r'C:\Users\AGNPT-M-001\AppData\Roaming\Multi Channel Systems\MC_Stimulus II'):
        untyped = True
        if untyped:
            Keyboard.type(word)
    t = Thread(target=test)
    t.start()
    t.join()

if __name__ == '__main__':
    test_key()
    test_type()