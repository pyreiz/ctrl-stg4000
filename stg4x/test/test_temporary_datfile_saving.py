# -*- coding: utf-8 -*-
"""
test temporary saving of stm files
"""
from stg4x.helper import tempdir
from stg4x.stm import PulseFile
def test_saving():
    dat = PulseFile()
    import os
    with tempdir() as dirpath:
        source_fname = os.path.join(dirpath, 'temporary.dat')
        dat.save(source_fname)            
        assert(os.path.exists(source_fname))
    assert(not os.path.exists(source_fname))