# -*- coding: utf-8 -*-
"""Interface to generate MCS II stm files"""
import os
from copy import deepcopy
# %%
class BaseDatFile():
    '''MCS II stmfiles 
    
    Allows the parametric generation of ascii-encoded stimfiles for MCS II    
    '''
    _hdr = ['Multi Channel Systems MC_Stimulus II\n',
       'ASCII import Version 1.10\n',
       '\n',
       'channels: 8\n',
       '\n',
       'output mode: current\n',
       '\n',
       'format: 4\n',
       '\n',
       'channel: 1\n',
       '\n',
       'value\ttime\n'] #: the header for every MCS II .dat file

    def _get_hdr(self):
        return self._hdr.copy()
    header = property(_get_hdr)

    def _set_lines(self, *args):
        '''Show error message when attempting to change lines directly
        
        .. hint::
            This function needs to be explicitly inherited to subclasses with super'''
        
        print('You can not change lines directly. Tweak the parameters instead')
        
    # --------------------    
    def save(self, source_name:str):
        'save the StimFile as .dat for loading with MCS II software'        
        if os.path.splitext(source_name)[1] != '.dat':
            raise ValueError('Only .dat files can be saved')
        os.makedirs(os.path.split(source_name)[0], exist_ok=True)
        with open(source_name, 'w') as f:
            for line in self.lines:
                f.write(line)
        self.source_name = source_name
               
class PulseFile(BaseDatFile):
    '''Bursting pulses subclass of :class:`.StimFile`
    '''
    
    def __init__(self, intensity=1000, mode='biphasic',
                 pulsewidth=200, burstcount=5, isi=2940):
        '''Create a new instance of a PulseFile with the given parameters

        Parameters can be changed arbitrarily, and the lines to be saved are 
        updated on the fly.        
        
        args
        ----
        intensity:int
        mode:str {'biphasic'}
            the mode to be used for the pulses
            'biphasic' : a pulse of specified intensity is immediatly followed 
                         by a second pulse with negative intensity with 
                         equal pulseduration,
            'monophasic': a single pulse            
        pulsewidth:int
            pulsewidth in µs, must be divisible by 20
        burstcount:int
            how often the pulse should be applied
        isi:int
            interstimulus interval in µs, must be divisible by 20

        '''
        self.isi = isi
        self.pulsewidth = pulsewidth
        self.burstcount = burstcount
        self.intensity = intensity
        self.mode = mode
        
    def __repr__(self):
        msg = (f'{self.__class__.__name__}(' + 
               f'intensity={self.intensity}, mode="{self.mode}", ' + 
               f'pulsewidth={self.pulsewidth}, burstcount={self.burstcount}, ' +
               f'isi={self.isi})')
        return msg
    
    # Intensity ----------------------
    def _get_int(self):
        return self._int
    
    def _set_int(self, intensity:float):
        if intensity > 16000:
            raise ValueError(f'Intensity of {intensity} is too high.' +
                             'Max is 16000µA')
        self._int = intensity
        self.compiled = False
    intensity = property(_get_int, _set_int)
    
    # Pulsewidth --------------------
    def _get_pw(self):
        return self._pw
    
    def _set_pw(self, pulsewidth:int):
        if pulsewidth%20 != 0:
            raise ValueError('Timesteps must be divisible by 20')
        self._pw = pulsewidth   
        self.compiled = False            
    pulsewidth = property(_get_pw, _set_pw)    
    
    
    # Burstcount --------------------
    def _get_bc(self):
        return self._bc
    
    def _set_bc(self, burstcount:int):
        if int(burstcount) == burstcount:
            self._bc = burstcount
        else:
            raise ValueError('Burstcount must be an integer')
        self.compiled = False            
    burstcount = property(_get_bc, _set_bc)

    # Interstimulus Interval  --------------------
    def _get_isi(self):
        return self._isi
    
    def _set_isi(self, isi:int):
        if isi%20 != 0:
            raise ValueError('Timesteps must be divisible by 20')
        self._isi = isi
        self.compiled = False            
    isi = property(_get_isi, _set_isi)
    
    # Mode --------------------
    def _get_mode(self):
        return self._mode
    
    def _set_mode(self, mode:str):
        if not mode in('biphasic', 'monophasic'):
            raise ValueError(f'Mode is {mode}, but ' + 
                             'can only be biphasic or monophasic')
        self._mode= mode
        self.compiled = False            
    mode = property(_get_mode, _set_mode)    

    # --------------------  
    def _generate_lines(self):
        stim_commands = []
        for bc in range(0, self.burstcount):
            newline = f'{self.intensity}\t{self.pulsewidth}\n'
            stim_commands.append(newline)    
            
            if self.mode == 'biphasic':
                newline = f'{-self.intensity}\t{self.pulsewidth}\n'
                stim_commands.append(newline)       
            elif self.mode == 'monophasic':
                pass
            else:
                raise ValueError('Mode is not recognized')
            
            newline = f'0\t{self.isi}\n'
            stim_commands.append(newline)    
                
        stim_info = self.header
        stim_info.extend(stim_commands)
        #stim_info.extend(stim_commands)    
        return stim_info
    
    def _duration(self):
        pw = self.pulsewidth 
        pw = (pw if self.mode =='monophasic' else pw*2)        
        return ((pw + self.isi) *self.burstcount)/(1000*1000)
    
    duration = property(_duration)
    
    def _set_lines(self, *args):
        super()._set_lines(*args)
    
    lines = property(_generate_lines, _set_lines)
    
    
    def as_single_pulse(self):
        stm = deepcopy(self)
        stm.burstcount = 1
        stm.isi = stm.pulsewidth
        return stm
