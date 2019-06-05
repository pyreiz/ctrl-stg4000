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
        self.connected = False

    @property
    def name(self):
        return self._info.DeviceName
    
    @property
    def version(self):
        with self.interface() as interface:
            _, soft, hard = interface.GetStgVersionInfo("","")
        return 'Hardware - {0} : Software - Version: {1}'.format(
                hard.replace('Rev.', 'Revision'),
                soft)

    @property
    def serial_number(self):
        return int(self._info.SerialNumber)

    @property
    def manufacturer(self):
        return self._info.Manufacturer
    
    def __repr__(self):
        return f"{str(self)} at {hex(id(self))}"
    
    def __str__(self):
        return self._info.ToString()

    def set_current_mode(self, channel_index:int=None):        
        if channel_index is None:
            with self.interface() as interface:
                interface.SetCurrentMode()
        else:
            with self.interface() as interface:
                interface.SetCurrentMode(System.UInt32(channel_index))
        
                
    def set_voltage_mode(self, channel_index:int=None):
        if channel_index is None:
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
        with self.interface() as interface:
            out = interface.GetNumberOfAnalogChannels()
        return out
    
    @property
    def trigin_count(self):
        with self.interface() as interface:
            out =  interface.GetNumberOfTriggerInputs()
        return out
    
    def stop_stimulation(self, channels:list=[1]):
        with self.interface() as interface:
            interface.SendStop(sum(channels))
        
    def start_stimulation(self, channels:list=[1]):
        with self.interface() as interface:
            interface.SendStart(sum(channels))

    def reset_triggers(self):
        channelmap = []
        syncoutmap = []
        repeat = []
        for chan_idx in range(0, self.channel_count):
            repeat.append(1) # every trigger only once
            syncoutmap.append(1 <<chan_idx) #diagonal triggerout
            channelmap.append(1 <<chan_idx) #diagonal triggerin
        with self.interface() as interface:
            interface.SetupTrigger(0, channelmap, syncoutmap, repeat);
    
    def download(self, channel_index:int=0, amplitude:list=[0], duration:list=[20], mode='current'):
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
        


