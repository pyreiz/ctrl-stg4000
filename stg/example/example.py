# -*- coding: utf-8 -*-
"""
Spyder Editor

This is a temporary script file.
"""
import clr
from pathlib import Path
import System
# %%
libpath = Path(__file__).parent.parent.parent
dllpath = libpath / "bin" / "McsUsbNet.dll"
fullPath = str(dllpath)
lib = System.Reflection.Assembly.LoadFile(fullPath)
print(lib.FullName)
print(lib.Location)
from Mcs.Usb import *
#%%
deviceList = CMcsUsbListNet()

deviceList.Initialize(DeviceEnumNet.MCS_STG_DEVICE)

print('Found {0:d} STGs'.format(deviceList.GetNumberOfDevices()))

for dev_num in range(0, deviceList.GetNumberOfDevices()):
   SerialNumber = deviceList.GetUsbListEntry(dev_num).SerialNumber
   print('Serial Number: {0:s}'.format(SerialNumber))


device = CStg200xDownloadNet()
device.Connect(deviceList.GetUsbListEntry(0))


device.SetVoltageMode();

Amplitude = ([+2000000, -2000000])  # Amplitude in uV
Duration = ([100000, 100000])  # Duration in us

AmplitudeNet = ([System.Int32(a) for a in Amplitude])
DurationNet  = ([System.UInt64(d) for d in Duration])

device.PrepareAndSendData(0, Amplitude, Duration, STG_DestinationEnumNet.channeldata_voltage)
device.SendStart(1)

device.PrepareAndSendData(1, Amplitude, Duration, STG_DestinationEnumNet.channeldata_voltage)
device.SendStart(2)
#
#device.Disconnect()
#
#del deviceList
#del device