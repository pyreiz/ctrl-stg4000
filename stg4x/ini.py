# -*- coding: utf-8 -*-
'MultiChanneSystems STGs'
import os as os
from threading import Lock
from configparser import ConfigParser
import logging
logger = logging.getLogger(__name__)
from shutil import copyfile
# %%
class mcsINI():
    '''Interface to the MCS Stimulus II ini-file'''
    
    iniFolder = os.path.join(os.path.expanduser('~'),
                      'AppData\Roaming\Multi Channel Systems\MC_Stimulus II') #: Default file position
    iniFile = 'MC_Stimulus II.ini'       
    filename = os.path.join(iniFolder, iniFile)
    lock = Lock()
    
    def __init__(self, overwrite_with=None):        
        if overwrite_with is not None:          
           self._replace(newfile=overwrite_with)
        
        if not os.path.exists(self.filename):
            raise FileNotFoundError('Could not find MCS Stimulus II ini file')
        
        self.cp = ConfigParser()
        self.cp.optionxform = str

    
    def replace_with(self, newfile:str):
        self.lock.acquire()
        [folder, fname] = os.path.split(newfile) 
        if fname != 'MC_Stimulus II.ini':
            raise ValueError('Filename invalid')            
        else:            
            copyfile(newfile, self.filename)            
        self.lock.release()
        
    def get_window(self):        
        self.read_file()
        setting = self.cp.get('MainFrame','WindowRect')
        x, y, w, h = [int(s) for s in setting.split(',')]
        return x,y,w,h

    def set_window(self, xpos:int=None, ypos:int=None, 
                       width:int=None, height:int=None):
        
        oldsetting = self.get_window()        
        newsetting = xpos, ypos, width, height
        setting = []
        for o,n in zip(oldsetting, newsetting):
            setting.append(o if n is None else n)
        mainsetting = ','.join(str(s)  for s in setting)
        setting[-2:] = [s//2 for s in setting[-2:]]
        childsetting = ','.join(str(s)  for s in setting)
        self.cp.set('MainFrame','WindowRect', mainsetting )        
        self.cp.set('Child','WindowRect', childsetting)
        self.cp.set('Child','Maximized', '0')
        if width == -1 and height == -1:
            self.cp.set('MainFrame','Maximized', '1')       
        else:
            self.cp.set('MainFrame','Maximized', '0')       
        self.write_file()
    
    def get_mf8_filenames(self):
        self.read_file()
        mf8_filenames = {}                
        for val, trigger in enumerate(range(0, 8, 1)):
            stmfile = self.cp.get('FileModeSettings', f'Trigger{trigger}')            
            mf8_filenames.update({val:stmfile})
        return mf8_filenames 

    def get_mf8(self):
        self.read_file()
        mf8 = {}                
        for val, trigger in enumerate(range(0, 8, 1)):
            stmfile = self.cp.get('FileModeSettings', f'Trigger{trigger}')
            if not os.path.exists(stmfile):                        
                logger.warning(
                        f'The stm file expected at {stmfile} does not exist.' + 
                        f'\nSolution: Check the MCS II Program')
                
            key = stmfile.split('\\')[-1].split('.')[0]
            mf8.update({key: val})
        return mf8 
    
    def set_mf8(self, settings:dict, common_folder:str=None):
        '''overwrite current mf8 settings with 
        
        args
        ----
        settings:dict (int, str)
            keys must be trigger value (0-7), values string of filename
        
        Example::
            settings= {0:'2mA.stm', 1:'4mA.stm', 2:'6mA.stm',3:'8mA.stm',
                       4:'10mA.stm', 5:'12mA.stm', 6:'14mA.stm',7:'16mA.stm'}
        
        '''        
        self.read_file()
        for trigger, stmfile in settings.items():        
            if common_folder:
                stmfile = os.path.join(common_folder, stmfile)
            if os.path.splitext(stmfile)[1] != '.stm':
                raise ValueError(f'{stmfile} is not an .stm')
            if not os.path.exists(stmfile):
                FileNotFoundError(f'{stmfile} not found')
            self.cp.set('FileModeSettings', f'Trigger{trigger}', stmfile)        
        self.write_file()
        
    def set_trigger(self, trigger:int, stmfile:str):        
        self.read_file()
        if not os.path.exists(stmfile):                        
            raise FileNotFoundError(
                    f'The stm file expected at {stmfile} does not exist.' + 
                    f'\nSolution: Check the path')
        self.cp.set('FileModeSettings', f'Trigger{int(trigger)}', stmfile)   
        self.write_file()
        
    def set_filemode(self, filemode:str):
        self.read_file()
        if filemode == 'mf8':
            self.cp.set('FileModeSettings','FileMode','MultiFileMode')
        elif filemode == 'single':
            self.cp.set('FileModeSettings','FileMode','SingleFileMode')
        else:
            raise NotImplementedError(f'{filemode} is not implemented')
        self.write_file() 
        
    def get_filemode(self):
        self.read_file()                
        mode = self.cp.get('FileModeSettings','FileMode')    
        return {'MultiFileMode':'mf8','SingleFileMode':'single'}.get(mode)
        
    def read_file(self):
        self.lock.acquire()
        self.cp.read(self.filename)
        self.lock.release()
        
    def write_file(self):
        self.lock.acquire()
        with open(self.filename, 'w') as f:
            self.cp.write(f, space_around_delimiters=False)
        self.lock.release()