# -*- coding: utf-8 -*-
"""

"""
# %%
from stg4x.stm import BaseDatFile
from stg4x.gui import mcsGUI
from stg4x.ini import mcsINI
import stg4x.helper as io
# %%
def compile_stm(dat:BaseDatFile, build_fname=None):
    import os
    dirpath = os.path.join(os.path.expanduser('~'),
                           'AppData\Roaming\Multi Channel Systems\MC_Stimulus II')     
    source_fname = os.path.join(dirpath, 'temporary.dat')
    dat.save(source_fname)         
    return compile_datfile(source_fname, build_fname)
        
# %%
def compile_datfile(source_fname, build_fname=None):
    if build_fname is None:
        import os
        dirpath = os.path.join(os.path.expanduser('~'),
                       'AppData\Roaming\Multi Channel Systems\MC_Stimulus II')     
        build_fname = os.path.join(dirpath, 'intervention.stm')
    gui = mcsGUI()   
    ini = mcsINI()
    gui.close()
    cur_fm = ini.get_filemode()
    ini.set_filemode('single')
    gui.open()        
    # make sure that dat file was written and released
    io.lock_until_file_is_safe(source_fname)
    gui.import_ascii(source_fname)      
    gui.sleep(1)
    if io.file_exists(build_fname):
       io.delete_file(build_fname) 
    gui.export_stm(build_fname)
    # lock until stm file was written and released
    io.lock_until_file_is_safe(build_fname)    
    gui.close()
    ini.set_filemode(cur_fm)
    return build_fname
