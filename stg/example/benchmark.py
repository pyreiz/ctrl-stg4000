# -*- coding: utf-8 -*-
"""
Created on Fri Dec 20 07:42:07 2019

@author: Messung
"""

from stg.api import STG4000Streamer
from arduino.onebnc import Arduino
import time

stg = STG4000Streamer()
print(stg, stg.version)
a = Arduino()
print(a.enquire())

# %%
stg.download(0,[1,-1, 0], [0.1, 0.1, 49.8])
while True:
    time.sleep(0.5)    
    a.trigger()
    
# %%
stg.download(0,[1,-1, 0], [0.1, 0.1, 49.8])
while True:
    time.sleep(0.5)    
    a.trigger()
    stg.start_stimulation([0])
# %%
while True:
    time.sleep(0.5)
    a.trigger()
    stg.download(0,[1,-1, 0], [0.1, 0.1, 49.8])    
    stg.start_stimulation([0])    

# %%
buffer_in_s=0.05
callback_percent=10
capacity_in_s=.1
stg.start_streaming(capacity_in_s=capacity_in_s, 
                    buffer_in_s=buffer_in_s,
                    callback_percent=callback_percent)
while True:
    stg.set_signal(0, amplitudes_in_mA=[0], durations_in_ms=[.1])
    time.sleep(0.5)    
    a.trigger()
    stg.set_signal(0, amplitudes_in_mA=[1, -1, 0], durations_in_ms=[.1, .1, 49.7])
    time.sleep(buffer_in_s * callback_percent/100)    
    
# %%