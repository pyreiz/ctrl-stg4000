# -*- coding: utf-8 -*-
"""Remote control the Mouse

Robert Guggenberger
"""
from sys import platform
if platform == 'win32':
    import win32api
    import win32con
#%%
class Mouse():
    
    
    @staticmethod
    def leftclick():
        'click the left mouse button'
        win32api.mouse_event(win32con.MOUSEEVENTF_LEFTDOWN |
                             win32con.MOUSEEVENTF_ABSOLUTE, 0, 0)
        win32api.mouse_event(win32con.MOUSEEVENTF_LEFTUP |
                             win32con.MOUSEEVENTF_ABSOLUTE, 0, 0)
        
    @staticmethod
    def rightclick():
        'click the left mouse button'
        win32api.mouse_event(win32con.MOUSEEVENTF_RIGHTDOWN |
                             win32con.MOUSEEVENTF_ABSOLUTE, 0, 0)        
        win32api.mouse_event(win32con.MOUSEEVENTF_RIGHTUP |
                             win32con.MOUSEEVENTF_ABSOLUTE, 0, 0)
        
    @staticmethod
    def move(x:int, y:int):
        'move mousecursorposition'
        win32api.SetCursorPos((x, y))
    
    @classmethod
    def left_click_at(cls, x:int, y:int):
        oldx, oldy= win32api.GetCursorPos()
        cls.move(x,y)
        cls.leftclick()
        cls.move(oldx, oldy)
    
    @staticmethod
    def get_pos():
        x,y = win32api.GetCursorPos()
        print(x,y)
        return x,y
 