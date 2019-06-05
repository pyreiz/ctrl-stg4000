# -*- coding: utf-8 -*-
"""
Created on Tue Jun  4 14:38:43 2019

@author: Robert Guggenberger
"""
from itertools import chain, repeat
# %%
class PulseFile():    
    '''STG4000 signal
    
    A thin wrapper for the parametric generation of stimulation signals
    '''
    
    def __init__(self,
                 intensity:int=1000, #in microamps, i.e. 1000 -> 1 mA
                 mode:str='biphasic',
                 pulsewidth:int=1, #in milliseconds, i.e. 10 -> 1ms
                 burstcount:int=1, 
                 isi:int=48): #in milliseconds, i.e. 48 -> 48ms
                
        if mode == 'biphasic':
            intensity = [intensity, -intensity]
            pulsewidth = [pulsewidth, pulsewidth]

        self.intensity = intensity
        self.mode = mode
        self.pulsewidth = pulsewidth
        self.burstcount = burstcount
        self.isi = isi
        

    def compile(self):    
        amps = [a for a in chain(self.intensity, [0])]        
        durs = [d for d in chain(self.pulsewidth, [self.isi])] 
        amps = chain(*repeat(amps, self.burstcount)) #repeat
        durs = chain(*repeat(durs, self.burstcount))# repeat 
        amps = [a for a in map(lambda x : x*1000, amps)] #scale to uA 
        durs = [d for d in map(lambda x : x*1000, durs)] #scale to us
        return amps, durs

    def __call__(self):
        return self.compile()
        