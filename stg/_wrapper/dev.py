from time import sleep
from math import sin, pi
import clr
from System import Array

from stg._wrapper.dll import (
    System,
    CMcsUsbListNet,
    CStg200xStreamingNet,
    STG_DestinationEnumNet,
    DeviceInfo,
    available,
)


class StreamingInterface:
    def __enter__(self):
        self.connect()
        return self

    def __exit__(self, type, value, tb):
        self.disconnect()

    def __init__(self, info, buffersize: int):
        self._info = info
        self._interface = CStg200xStreamingNet(System.UInt32(buffersize))

    def connect(self):
        self.connected = True
        self._interface.Connect(self._info)

    def disconnect(self):
        self.connected = False
        self._interface.Disconnect()

    def __getattr__(self, item):
        return getattr(self._interface, item)


def send_data(interface, amp: float, length: int):
    nTrigger = device.GetNumberOfTriggerInputs()
    for chan in range(nTrigger):
        space = device.GetDataQueueSpace(chan)
        #  while space < length:
        #      sleep(0.01)
        #      space = device.GetDataQueueSpace(chan)
        if space > length:
            signal = []
            for i in range(length):
                # sample = amp * 30_000 * sin(2 * pi / 1000 * (chan + 1) * i)
                sample = amp * 30_000 * 1
                signal.append(sample)
            device.EnqueueData(chan, Array[System.Int16](signal))
            space = device.GetDataQueueSpace(chan)


def queue(device, chan: int = 0, amp: float = 1, pulsewidth: int = 100):
    space = device.GetDataQueueSpace(chan)
    if space < pulsewidth:
        return 0
    signal = []
    for i in range(pulsewidth):
        sample = amp * 1000  # * 30_000 * 1
        signal.append(sample)
    device.EnqueueData(chan, Array[System.Int16](signal))
    return space - device.GetDataQueueSpace(chan)


info = available()[0]
buffer_size = 2_000
device = StreamingInterface(info, buffer_size)
device.connect()
# device.SetVoltageMode()
device.SetCurrentMode()
device.EnableContinousMode()
# device.SetOutputRate(System.UInt32(2000))
total_memory = device.GetTotalMemory()
print(total_memory)
nTrigger = device.GetNumberOfTriggerInputs()
trigger_capacity = [System.UInt32(100) for i in range(nTrigger)]
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


device.StartLoop()
sleep(1)
for i in range(nTrigger):
    device.SendStart(System.UInt32(i))


def state():
    while True:
        # yield from [0, 0.25, 0, 0.5, 0, 0.75, 0, 1, 0, 0.75, 0, 0.5]
        yield from [0, 1]


device.SetOutputRate(System.UInt32(1000))
cbs = state()
print("Start stimulation")
try:
    while True:
        amp = next(cbs)
        while not queue(device, chan=0, amp=amp, pulsewidth=1):
            pass
        while not queue(device, chan=0, amp=0, pulsewidth=99):
            pass

except Exception:
    for i in range(nTrigger):
        device.SendStop(System.UInt32(i))

    device.StopLoop()
    device.disconnect()

device.GetFramesDone()
device.GetCurrentRate(0)
device.GetCurrentRate(0)
device.GetFramesBuffered(0)
