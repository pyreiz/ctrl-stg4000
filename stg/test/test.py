# -*- coding: utf-8 -*-
"""
Created on Tue Jun  4 17:20:42 2019

@author: Messung
"""

if __name__ == '__main__':
    from stg import PulseFile, STG4000
    
    stg =  STG4000()
    print(stg, stg.version)
    p = PulseFile()
    
    stg.download(0, *p())    
    stg.start_stimulation([1])
    
    stg.sleep(0.5)
    p = PulseFile(intensity=1000, burstcount=60)
    stg.download(0, *p()) 
    stg.start_stimulation([1])
    
    
    for i in range(0, 100, 1):
        p = PulseFile(intensity=1000, pulsewidth=1*i)
        stg.download(0, *p()) 
        stg.start_stimulation([1])
        stg.sleep(0.5)
        