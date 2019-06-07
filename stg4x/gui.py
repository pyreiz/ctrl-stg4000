# -*- coding: utf-8 -*-
"""GUI control
"""
from stg4x.control.mouse import Mouse
from stg4x.control.keyboard import Keyboard
from threading import Lock
from stg4x.ini import mcsINI
from time import sleep
from subprocess import Popen
#%%
class mcsGUI():    
    'Class resembling the MC Stimulus II GUI'
    lock = Lock() #: singleton, there can only be one GUI ever
    isOpen = [False]    
    def __init__(self, cmd:str=None) -> None:
        xpos = 0
        ypos = 0
        width = 600
        height = 400
        ini = mcsINI()        
        ini.set_window(xpos, ypos, width, height)
        if cmd is not None:
            self.cmd = cmd
        else:
            from stg4x.helper import find_file
            self.cmd = find_file(name='MC_Stimulus.exe', 
                                 path='C:\Program Files (x86)\Multi Channel Systems')
                    
    def acquire(self):
        self.lock.acquire()        
        
    def release(self):
        self.lock.release()        
    
    def boot(self):
        self.close()
        self.open()
        
    def open(self):
        if self.isOpen[0]:
            self.close()                
        Popen(self.cmd)
        sleep(2)
        self.isOpen[0] = True

    def close(self):
        if all_guis_killed():
            self.isOpen[0] = False
            
            
    def import_ascii(self, fname):
        Mouse.left_click_at(20,60)
        Mouse.left_click_at(20,40)
        Mouse.left_click_at(20,180)       
        Keyboard.type(fname)
        Keyboard.press('enter')
        Keyboard.release('enter')
        sleep(1)
        
    def export_stm(self, cname):
        Mouse.left_click_at(20,40)
        Mouse.left_click_at(20,150)                
        Keyboard.type(cname)
        Keyboard.press('enter')        
        sleep(1)

    def download(self):      
        Mouse.left_click_at(233, 74)

    def trigger_now(self, channel:int):
        xpos = int(330+channel*20)
        Mouse.left_click_at(xpos, 90)

    
    def sleep(self, duration:float):
        sleep(duration)
# %%
def all_guis_killed():
    import os
    os.system('taskkill /IM MC_Stimulus.exe /F')
    return True
