# -*- coding: utf-8 -*-
import os
from warnings import warn
import ctypes
import win32ui
from threading import Barrier, Thread
import contextlib
import shutil
import tempfile
#%%
def lock_until_file_is_safe(filename):
    opened = False
    while not opened:
        try:
            with open(filename):
                opened=True
        except (FileNotFoundError, PermissionError):
            pass
    return True

def lock_until_files_are_safe(filenames):
    def lock(f, b):
        lock_until_file_is_safe(f)
        b.wait()
        
    barrier = Barrier(len(filenames)+1)
    for filename in filenames:
        t = Thread(target=lock, args=(filename, barrier, ))
        t.start()
    barrier.wait()

def file_exists(path):
    return os.path.exists(path)

def delete_file(fname):
    return os.remove(fname)    

def assert_file_exists(path):
    try:
        assert(file_exists)    
    except AssertionError as e:
        print('{0} was not found'.format(path))
        raise e    
    return True

def is_file(filename: str, ext: str) -> (bool, str):
    cur_ext = os.path.splitext(filename)[1]
    if not cur_ext == ext:
        warn('''Filename does not end in {0}. \r
              Warning: I change extension to {0}'''.format(ext))
        return False, filename.replace(cur_ext, ext)
    else:
        return True, filename
#%%
def find_file(name:str, path:str=None):
    '''finds and returns the path to a file with given name
    args
    ----
    name:str
        name of the file to search
    path:str
        folder to start looking, defaults to root (e.g. C:\\ or \)
        
    returns
    -------
    path:str
        path to file with given name
    '''
    
    if path is None:
        path = os.path.abspath(os.sep)
        
    for root, dirs, files in os.walk(path):
        if name in files:
            return os.path.join(root, name)
#%%
def list_all_window_titles():
     
    EnumWindows = ctypes.windll.user32.EnumWindows
    EnumWindowsProc = ctypes.WINFUNCTYPE(ctypes.c_bool, ctypes.POINTER(ctypes.c_int), ctypes.POINTER(ctypes.c_int))
    GetWindowText = ctypes.windll.user32.GetWindowTextW
    GetWindowTextLength = ctypes.windll.user32.GetWindowTextLengthW
    IsWindowVisible = ctypes.windll.user32.IsWindowVisible
     
    titles = []
    def foreach_window(hwnd, lParam):
        if IsWindowVisible(hwnd):
            length = GetWindowTextLength(hwnd)
            buff = ctypes.create_unicode_buffer(length + 1)
            GetWindowText(hwnd, buff, length + 1)
            titles.append(buff.value)
        return True
    EnumWindows(EnumWindowsProc(foreach_window), 0)
 
    return titles


def window_exists(classname):
    try:
        win32ui.FindWindow(None, classname)
    except win32ui.error:
        return False
    else:
        return True
    
def assert_window_exists(window_title):
    try:
        assert(window_exists(window_title))
    except AssertionError as e:
        print('{0} was not found'.format(window_title))
        raise e    
    return True
# %%
@contextlib.contextmanager
def cd(newdir, cleanup=lambda: True):
    prevdir = os.getcwd()
    os.chdir(os.path.expanduser(newdir))
    try:
        yield
    finally:
        os.chdir(prevdir)
        cleanup()

@contextlib.contextmanager
def tempdir():
    dirpath = tempfile.mkdtemp()
    def cleanup():
        shutil.rmtree(dirpath)
    with cd(dirpath, cleanup):
        yield dirpath

#%%
def make_library(pathdir:str):
    d = {}
    for fname in os.listdir(pathdir):
        if os.path.splitext(fname)[1] =='.stm':
            key = os.path.splitext(fname)[0]
            val = os.path.join(pathdir, fname)
            print(f'Create {key} linking to {val}')
            d[key] = val
    return d
        
            
            