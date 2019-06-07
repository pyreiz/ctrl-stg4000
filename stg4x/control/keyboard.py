"""Remote control the keyboard

Robert Guggenberger
"""
from sys import platform
if platform == 'win32':
    import win32api
    import win32con
# %%    
  #Giant dictonary to hold key name and VK value
    VK_CODE = {'backspace':0x08,
               'tab':0x09,
               'clear':0x0C,
               'enter':0x0D,
               'shift':0x10,
               'ctrl':0x11,
               'alt':0x12,
               'alt-gr':165,
               'pause':0x13,
               'caps_lock':0x14,
               'esc':0x1B,
               'spacebar':0x20,
               'page_up':0x21,
               'page_down':0x22,
               'end':0x23,
               'home':0x24,
               'left_arrow':0x25,
               'up_arrow':0x26,
               'right_arrow':0x27,
               'down_arrow':0x28,
               'select':0x29,
               'print':0x2A,
               'execute':0x2B,
               'print_screen':0x2C,
               'ins':0x2D,
               'del':0x2E,
               'help':0x2F,
               'numpad_0':0x60,
               'numpad_1':0x61,
               'numpad_2':0x62,
               'numpad_3':0x63,
               'numpad_4':0x64,
               'numpad_5':0x65,
               'numpad_6':0x66,
               'numpad_7':0x67,
               'numpad_8':0x68,
               'numpad_9':0x69,
               'multiply_key':0x6A,
               'add_key':0x6B,
               'separator_key':0x6C,
               'subtract_key':0x6D,
               'decimal_key':0x6E,
               'divide_key':0x6F,
               'F1':0x70,
               'F2':0x71,
               'F3':0x72,
               'F4':0x73,
               'F5':0x74,
               'F6':0x75,
               'F7':0x76,
               'F8':0x77,
               'F9':0x78,
               'F10':0x79,
               'F11':0x7A,
               'F12':0x7B,
               'F13':0x7C,
               'F14':0x7D,
               'F15':0x7E,
               'F16':0x7F,
               'F17':0x80,
               'F18':0x81,
               'F19':0x82,
               'F20':0x83,
               'F21':0x84,
               'F22':0x85,
               'F23':0x86,
               'F24':0x87,
               'num_lock':0x90,
               'scroll_lock':0x91,
               'left_shift':0xA0,
               'right_shift ':0xA1,
               'left_control':0xA2,
               'right_control':0xA3,
               'left_menu':0xA4,
               'right_menu':0xA5,
               'browser_back':0xA6,
               'browser_forward':0xA7,
               'browser_refresh':0xA8,
               'browser_stop':0xA9,
               'browser_search':0xAA,
               'browser_favorites':0xAB,
               'browser_start_and_home':0xAC,
               'volume_mute':0xAD,
               'volume_Down':0xAE,
               'volume_up':0xAF,
               'next_track':0xB0,
               'previous_track':0xB1,
               'stop_media':0xB2,
               'play/pause_media':0xB3,
               'start_mail':0xB4,
               'select_media':0xB5,
               'start_application_1':0xB6,
               'start_application_2':0xB7,
               'attn_key':0xF6,
               'crsel_key':0xF7,
               'exsel_key':0xF8,
               'play_key':0xFA,
               'zoom_key':0xFB,
               'clear_key':0xFE}

notupper = [str(i) for i in range(0,10,1)]
notupper.append('.')

def keycode(key):
        try:
            keycode = VK_CODE[key]
        except KeyError:
            keycode = win32api.VkKeyScan(key)        
        return keycode
    
class Keyboard():  
    
    @staticmethod
    def release(key):
        '''
        release a key.
        '''
        win32api.keybd_event(keycode(key), 0, win32con.KEYEVENTF_KEYUP, 0)
    
    @staticmethod
    def press(key):
        '''
        press and hold. Do NOT release.
        '''        
        win32api.keybd_event(keycode(key), 0, 0, 0)
               
    @classmethod
    def press_release(cls, key):
        '''
        press and hold passed in strings. Once held, release
        '''        
        cls.press(key)        
        cls.release(key)

        
    @classmethod
    def _type(cls, *keys):
        for key in keys:                     
            if key == '\\':
                cls.press('alt-gr')
                cls.press('ß')
                cls.release('ß')
                cls.release('alt-gr')   
            elif key == '_':
                cls.press('shift')
                cls.press('_')
                cls.release('_')
                cls.release('shift')
            elif key =='-':
                cls.press_release(key)
            elif key == key.upper() and key not in notupper:
                cls.press('shift')
                cls.press_release(key)
                cls.release('shift')
            else:
                cls.press_release(key)
    
    @classmethod
    def type(cls, word):
        cls._type(*tuple(word))

    
        