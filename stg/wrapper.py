# -*- coding: utf-8 -*-
"""
Spyder Editor

This is a temporary script file.
"""
import clr
from pathlib import Path
import System
libpath = Path(__file__).parent.parent
dllpath = libpath / "bin" / "McsUsbNet.dll"
fullPath = str(dllpath)
lib = System.Reflection.Assembly.LoadFile(fullPath)
from Mcs.Usb import *
from functools import lru_cache
from time import sleep
from typing import List
# %%
def available(serial:int=None):
    deviceList = CMcsUsbListNet()
    deviceList.Initialize(DeviceEnumNet.MCS_STG_DEVICE)
    if serial is None: #return a list of all available
        devices = []
        for dev_num in range(0, deviceList.GetNumberOfDevices()):
            devices.append(deviceList.GetUsbListEntry(dev_num))            
        return devices
        
    else: #return the device with the desired serial number
        device = None
        for dev_num in range(0, deviceList.GetNumberOfDevices()):        
            ser = int(deviceList.GetUsbListEntry(dev_num).SerialNumber)
            if ser == serial:
                device = deviceList.GetUsbListEntry(dev_num)            
        return device
       
        
class BasicInterface():
    
    def __enter__(self):
        self.connect()
        return self
    
    def __exit__(self, type, value, tb):
        self.disconnect()        
        
    def __init__(self, info):
        self._info = info
        self._interface = CStg200xDownloadNet()
        
    def connect(self):
        self.connected = True
        self._interface.Connect(self._info)
        
    def disconnect(self):
        self.connected = False
        self._interface.Disconnect()
        
    def __getattr__(self, item):
        return getattr(self._interface, item)


def bitmap(valuelist:list):
    bmap = sum(map(lambda x: 2**x, valuelist)) 
    return None if bmap == 0 else bmap
            
            
class STG4000():

    def sleep(self, duration:float):
        sleep(duration)
        
    def __init__(self, serial:int=None):
        if serial is None:
            info = available()[0]
        else:
            info = available(serial)
        print('Selecting {0:s}:SN {1:s}'.format(info.DeviceName, info.SerialNumber))            
        self._info = info
        self.interface = lambda: BasicInterface(info)
        self.diagonalize_triggermap()

    @property
    def name(self):
        "returns the model name, i.e. STG4002/4/8"
        return self._info.DeviceName
    
    @property
    def version(self):    
        "Returns the current hardware and software version"
        soft, hard = self._version
        return 'Hardware - {0} : Software - Version: {1}'.format(
                hard.replace('Rev.', 'Revision'),
                soft)
    @property
    def _version(self):
        with self.interface() as interface:
            _, soft, hard = interface.GetStgVersionInfo("","")
        return soft, hard

    @property
    def serial_number(self):
        "Returns the serial number of the device"
        return int(self._info.SerialNumber)

    @property
    def manufacturer(self):
        "Returns the name of the manufacturer"
        return self._info.Manufacturer
    
    def __repr__(self):
        return f"{str(self)} at {hex(id(self))}"
    
    def __str__(self):
        return self._info.ToString()

    def set_current_mode(self, channel_index:int=all):   
        """set a single or all channels to current mode
        
        args
        ----
        channel_index:list
            defaults to all, which sets all channels to current mode
            otherwise, takes an integer of the target channel.
            Indexing starts at 0.        
        """
        if channel_index is all:
            with self.interface() as interface:
                interface.SetCurrentMode()
        else:
            with self.interface() as interface:
                interface.SetCurrentMode(System.UInt32(channel_index))
        
                
    def set_voltage_mode(self, channel_index:int=all):
        """set a single or all channels to voltage mode
        
        args
        ----
        channel_index:list
            defaults to all, which sets all channels to voltage mode
            otherwise, takes an integer of the target channel.
            Indexing starts at 0.
        
        """
        if channel_index is all:
            with self.interface() as interface:
                interface.SetVoltageMode()
        else:
            with self.interface() as interface:
                interface.SetVoltageMode(System.UInt32(channel_index))
        
    @property
    def current_resolution_in_uA(self):
        with self.interface() as interface:
            out = (interface.GetCurrentResolutionInNanoAmp(System.UInt32(0)) / 
                   1000)
        return out

    @property
    def current_resolution_in_mA(self):
        with self.interface() as interface:
            out = (interface.GetCurrentResolutionInNanoAmp(System.UInt32(0)) / 
                   (1000*1000))
        return out
    
    @property
    def current_range_in_mA(self):
        with self.interface() as interface:
            out = (interface.GetCurrentRangeInNanoAmp(System.UInt32(0))/
                   (1000*1000))
        return out

    @property
    def current_range_in_uA(self):
        with self.interface() as interface:
            out = (interface.GetCurrentRangeInNanoAmp(System.UInt32(0))/
                   (1000))
        return out

    @property
    def voltage_resolution_in_uV(self):
        with self.interface() as interface:
            out = (interface.GetVoltageResolutionInMicroVolt(System.UInt32(0)))
        return out    
        
    @property
    def voltage_range_in_mV(self):
        with self.interface() as interface:
            out = (interface.GetVoltageRangeInMicroVolt(System.UInt32(0)) / 
                 (1000))
        return out
    
    @property
    def time_resolution_in_us(self):
        return 20
    
    @property
    def time_resolution_in_ms(self):
        return 0.02
    
    @property
    def DAC_resolution(self):
        with self.interface() as interface:
            out = interface.GetDACResolution()
        return out
        
    @property
    def channel_count(self):
        "returns the number of stimulation channels"
        with self.interface() as interface:
            out = interface.GetNumberOfAnalogChannels()
        return out
    
    @property
    def trigin_count(self):
        "returns the number of  trigger inputs"
        with self.interface() as interface:
            out =  interface.GetNumberOfTriggerInputs()
        return out
    
    def stop_stimulation(self, targets:list=all):   
        """stops all trigger inputs or a selection based on a list 
        
        Triggers are mapped to channels according to the channelmap.
        Use `~STG4000.diagonalize_triggermap` to normalize the mapping of trigger 
        to channel to the diagonal identity, i.e. trigin 0 triggers channel 
        0 and so on.
        
        args
        ----
        channel_index:list
            defaults to all, which sets all channels to voltage mode
            otherwise, takes a list of integers of the targets, 
            e.g. [0,1]
            Indexing starts at 0.
        
        """
        
        if targets is all:
            targets = [c for c in range(self.channel_count)]
        with self.interface() as interface:
            interface.SendStop(System.UInt32(bitmap(targets)))
        
    def start_stimulation(self, channels:list=all):
        """starts all trigger inputs or a selection based on a list 
        
        Triggers are mapped to channels according to the channelmap.
        Use `~STG4000.diagonalize_triggermap` to normalize the mapping of trigger 
        to channel to the diagonal identity, i.e. trigin 0 triggers channel 
        0 and so on.
        
        args
        ----
        channel_index:list
            defaults to all, which sets all channels to voltage mode
            otherwise, takes a list of integers of the targets, 
            e.g. [0,1]
            Indexing starts at 0.
        
        """
        
        if channels is all:
            channels= [c for c in range(self.channel_count)]
        with self.interface() as interface:
            interface.SendStart(System.UInt32(bitmap(channels)))

    def diagonalize_triggermap(self):
        """Normalize the channelmap to a diagonal
                
        Triggers are mapped to channels according to the channelmap. This is 
        done at the lower level with interface.SetupTrigger. 
        
        Use this function to normalize the mapping of trigger to channel to the 
        diagonal identity, i.e. trigin 0 triggers channel 0 and so on.
        
        """
        channelmap = []
        syncoutmap = []
        repeat = []
        for chan_idx in range(0, self.channel_count):
            repeat.append(1) # every trigger only once
            syncoutmap.append(1 <<chan_idx) #diagonal triggerout
            channelmap.append(1 <<chan_idx) #diagonal triggerin
        with self.interface() as interface:
            interface.SetupTrigger(0, channelmap, syncoutmap, repeat);        
    
    def download(self, channel_index:List[int,]=0, amplitude:List[int,]=[0], 
                 duration:list=[20], mode='current'):
        """Download a stimulation signal 
        
        The signal is compressed to amplitudes and their respective durations 
        
        args
        ----
        
        channel_index:int
            The index of the channel for which to download the signal. Indexing
            starts at 0
        amplitude:List[int,]
            a list of amplitudes in µA/µV delivered for the corresponding duration 
        duration:List[int,]
            a list of durations in µs determing how long each corresponding 
            amplitude is delivered
        mode:str {'current', 'voltage'}
            whether the channel should be current or voltage controlled. Based
            on this the units of amplitude are µA (current) or µV (voltage).        
        
        
        
        notes:
           The signal is downloaded with  interface.PrepareAndSendData, 
           therefore previous data sent to that channel is erased first.
        """
        if len(amplitude) != len(duration):
            raise ValueError("Every amplitude needs a duration and vice versa!")
        amplitude = ([System.Int32(a) for a in amplitude])
        duration  = ([System.UInt64(d) for d in duration])

        if mode == "current":
            self.set_current_mode(channel_index)
            with self.interface() as interface:           
                interface.PrepareAndSendData(channel_index, amplitude, duration,
                                             STG_DestinationEnumNet.channeldata_current)
        elif mode == "voltage":
            self.set_voltage_mode(System.UInt32(channel_index))
            with self.interface() as interface:           
                interface.PrepareAndSendData(channel_index, amplitude, duration,
                                             STG_DestinationEnumNet.channeldata_voltage)
        


