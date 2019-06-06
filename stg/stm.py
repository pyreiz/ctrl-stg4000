# -*- coding: utf-8 -*-
"""
Created on Tue Jun  4 14:38:43 2019

@author: Robert Guggenberger
"""
from itertools import chain, repeat
from pathlib import Path
# %%
def init_datfile(filename:str="~/Desktop/test.dat"):
    fname = Path(str(filename)).expanduser().absolute()
    if fname.suffix == "":
        fname = fname.with_suffix(".dat")    
    if fname.suffix != ".dat":
        raise ValueError('Only .dat files can be saved')
        
    stim_info = ['Multi Channel Systems MC_Stimulus II\n',
                 'ASCII import Version 1.10\n',
                 '\n',
                 'channels: 2\n',
                 '\n',
                 'output mode: current\n',
                 '\n',
                 'format: 4\n',
                 '\n'
                 ] #: the header for every MCS II .dat file
    
    with fname.open('w') as f:
        for line in stim_info:
            f.write(line)
# ---------
    
def encode(pulsefile, channel:int=0):
    """encode a pulsefile into ascii format
    
    args
    ----
    pulsefile:PulseFile
        a pulsefile
    channel:int
        the channel, indexing starts at 0
    """
    stim_info = [f'channel: {channel+1}\n',
                 '\n',
                 'value\ttime\n'] #: the header for every channel

    stim_commands = []
    for bc in range(0, pulsefile.burstcount):
        for amp, pw in zip(pulsefile.intensity, pulsefile.pulsewidth):
            newline = f'{amp}\t{pw*1000}\n' #scale to µA/µs

            stim_commands.append(newline)    
        
        newline = f'0\t{pulsefile.isi*1000}\n' #scale to µs
        stim_commands.append(newline)    
        
    stim_info.extend(stim_commands)
    return stim_info

def dump(filename:str="~/Desktop/test.dat", *pulsefiles):
    fname = Path(str(filename)).expanduser().absolute()
    init_datfile(fname)
    with fname.open('r') as f:
        lines = f.readlines()
    for idx, pulsefile in enumerate(pulsefiles):
        if idx>0:
            lines.append('\n')
        lines.extend(encode(pulsefile, channel=idx))
    with fname.open('w') as f:
        for line in lines:
            f.write(line)
            

# --------
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

    def dump(self, fname):
        dump(fname,self)
# %%

    
        