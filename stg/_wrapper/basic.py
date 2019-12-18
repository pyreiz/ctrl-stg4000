import clr
import System
from stg.install import DLLPATH
from typing import List
from time import sleep

lib = System.Reflection.Assembly.LoadFile(str(DLLPATH))
from Mcs.Usb import (
    CMcsUsbListNet,
    DeviceEnumNet,
    CStg200xStreamingNet,
    CStg200xDownloadNet,
    STG_DestinationEnumNet,
)
from Mcs.Usb import CMcsUsbListEntryNet as DeviceInfo
from System import Array

# ------------------------------------------------------------------------------
def available() -> List[DeviceInfo]:
    "list all available MCS STGs connected over USB with this PC"
    deviceList = CMcsUsbListNet()
    deviceList.Initialize(DeviceEnumNet.MCS_STG_DEVICE)
    devices = []
    for dev_num in range(0, deviceList.GetNumberOfDevices()):
        devices.append(deviceList.GetUsbListEntry(dev_num))
    return devices


def pulsate(device, chan: int = 0, amp: float = 1, pulsewidth: int = 100):
    space = device.GetDataQueueSpace(chan)
    if space < pulsewidth:
        return 0
    signal = []
    for i in range(pulsewidth):
        sample = amp * 1000  # * 30_000 * 1
        signal.append(sample)
    device.EnqueueData(chan, Array[System.Int16](signal))
    return space - device.GetDataQueueSpace(chan)


def queue(device, signal: List[int], chan: int = 0):
    space = device.GetDataQueueSpace(chan)
    if space < len(signal):
        return 0
    device.EnqueueData(chan, Array[System.Int16](signal))
    return space - device.GetDataQueueSpace(chan)


def connect(device, info):
    err = device.Connect(info)
    if err != 0:
        raise ConnectionError(
            "Error {0:f} for {1:s}:SN {2:s}".format(
                err, info.DeviceName, info.SerialNumber
            )
        )
    else:
        print(
            "Connected successfully with {0:s}:SN {1:s}".format(
                info.DeviceName, info.SerialNumber
            )
        )
    return device.GetNumberOfTriggerInputs()


def set_capacity(device, capacity: int, channel: int = 0):
    total_memory = device.GetTotalMemory()
    print(total_memory)
    nTrigger = device.GetNumberOfTriggerInputs()
    trigger_capacity = []
    for i in range(nTrigger):
        if i == channel:
            trigger_capacity.append(System.UInt32(capacity))
        else:
            trigger_capacity.append(System.UInt32(1))

    device.SetCapacity(trigger_capacity)
    cmap = []
    syncmap = []
    digoutmap = []
    autostart = []
    callback_threshold = []
    for i in range(nTrigger):
        cmap.append(System.UInt32(1 << i))
        syncmap.append(System.UInt32(0 << i))  # no syncout
        digoutmap.append(System.UInt32(1 << i))
        autostart.append(System.UInt32(0))  #
        callback_threshold.append(System.UInt32(0))  # 50% of buffersize
    callback_threshold[0] = System.UInt32(10)  # 50% of buffersize
    device.SetupTrigger(cmap, syncmap, digoutmap, autostart, callback_threshold)


def state():
    while True:
        yield from [0, 0.25, 0, 0.5, 0, 0.75, 0, 1, 0, 0.75, 0, 0.5]
        # yield from [0, 1]


# ------------------
if __name__ == "__main__":
    info = available()[0]

    buffer_size = 50_000
    device = CStg200xStreamingNet(System.UInt32(buffer_size))
    nTrigger = connect(device, info)

    # device.SetVoltageMode()
    device.SetCurrentMode()
    # device.EnableContinousMode()
    device.DisableContinousMode()

    rate = 50_000
    set_capacity(device, rate, 0)
    device.SetOutputRate(System.UInt32(rate))

    device.StartLoop()
    sleep(1)
    for i in range(nTrigger):
        device.SendStart(System.UInt32(i))

    print("Start stimulation")
    try:
        cbs = state()
        while True:
            # while not queue(device, signal=[1000] + [0, 0] * int(rate / 100), chan=0):
            amp = next(cbs)
            while not queue(device, signal=[1000 * amp] + [0, 0], chan=0):
                pass

    except Exception as e:
        print(e)
        for i in range(nTrigger):
            device.SendStop(System.UInt32(i))

        device.StopLoop()
        device.Disconnect()
