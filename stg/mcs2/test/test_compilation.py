# -*- coding: utf-8 -*-
"""
test compilation
"""
from stg4x.stg import compile_datfile, compile_stm
from stg4x.stm import PulseFile

def test_compilation():    
    stm = PulseFile()
    import os    #
    dirpath = os.path.join(os.path.expanduser('~'),
                      'AppData\Roaming\Multi Channel Systems\MC_Stimulus II')
    build_fname = os.path.join(dirpath, 'temporary.stm')
    source_fname = os.path.join(dirpath, 'temporary.dat')
    stm.save(source_fname)        
    compile_datfile(source_fname, build_fname)
    os.path.exists(build_fname)
    os.remove(build_fname)
    
def test_compilation_direct():    
    stm = PulseFile()
    import os    #    
    dirpath = os.path.join(os.path.expanduser('~'),
                      'AppData\Roaming\Multi Channel Systems\MC_Stimulus II')
    build_fname = os.path.join(dirpath, 'temporary.stm')    
    compile_stm(stm, build_fname)           
    os.path.exists(build_fname)
    os.remove(build_fname)