from time import sleep
from math import sin, pi
from stg._wrapper.dll import (
    System,
    CMcsUsbListNet,
    CStg200xStreamingNet,
    STG_DestinationEnumNet,
    DeviceInfo,
    available,
    bitmap,
)
from typing import List


def bitmap(valuelist: list):
    bmap = sum(map(lambda x: 2 ** x, valuelist))
    return None if bmap == 0 else bmap


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


class STG4000:
    def sleep(self, duration: float):
        sleep(duration)

    def __init__(self, serial: int = None, buffer_size: int = 50_000):
        if serial is None:
            info = available()[0]
        else:
            info = select(serial)
        print("Selecting {0:s}:SN {1:s}".format(info.DeviceName, info.SerialNumber))
        self._info = info
        self.interface = lambda: StreamingInterface(info, buffer_size)
        self.buffer_size = buffer_size
        self.diagonalize_triggermap()
        self.set_capacity()

    def set_capacity(self):
        with self.interface() as interface:
            # total_memory = interface.GetTotalMemory()
            nTrigger = interface.GetNumberOfTriggerInputs()
            trigger_capacity = [
                System.UInt32(self.buffer_size) for i in range(nTrigger)
            ]
            interface.SetCapacity(trigger_capacity)

    @property
    def name(self):
        "returns the model name, i.e. STG4002/4/8"
        return self._info.DeviceName

    @property
    def version(self):
        "Returns the current hardware and software version"
        soft, hard = self._version
        return "Hardware - {0} : Software - Version: {1}".format(
            hard.replace("Rev.", "Revision"), soft
        )

    @property
    def _version(self):
        with self.interface() as interface:
            _, soft, hard = interface.GetStgVersionInfo("", "")
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

    def set_current_mode(self, channel_index: List[int] = []):
        """set a single or all channels to current mode
        
        args
        ----
        channel_index:list
            defaults to all, which sets all channels to current mode
            otherwise, takes an integer of the target channel.
            Indexing starts at 0.        
        """
        if channel_index == []:
            with self.interface() as interface:
                interface.SetCurrentMode()
        else:
            with self.interface() as interface:
                interface.SetCurrentMode(System.UInt32(channel_index))

    def set_voltage_mode(self, channel_index: List[int] = []):
        """set a single or all channels to voltage mode
        
        args
        ----
        channel_index:list
            defaults to all, which sets all channels to voltage mode
            otherwise, takes an integer of the target channel.
            Indexing starts at 0.
        
        """
        if channel_index == []:
            with self.interface() as interface:
                interface.SetVoltageMode()
        else:
            with self.interface() as interface:
                interface.SetVoltageMode(System.UInt32(channel_index))

    @property
    def current_resolution_in_uA(self):
        with self.interface() as interface:
            out = interface.GetCurrentResolutionInNanoAmp(System.UInt32(0)) / 1000
        return out

    @property
    def current_resolution_in_mA(self):
        with self.interface() as interface:
            out = interface.GetCurrentResolutionInNanoAmp(System.UInt32(0)) / (
                1000 * 1000
            )
        return out

    @property
    def current_range_in_mA(self):
        with self.interface() as interface:
            out = interface.GetCurrentRangeInNanoAmp(System.UInt32(0)) / (1000 * 1000)
        return out

    @property
    def current_range_in_uA(self):
        with self.interface() as interface:
            out = interface.GetCurrentRangeInNanoAmp(System.UInt32(0)) / (1000)
        return out

    @property
    def voltage_resolution_in_uV(self):
        with self.interface() as interface:
            out = interface.GetVoltageResolutionInMicroVolt(System.UInt32(0))
        return out

    @property
    def voltage_range_in_mV(self):
        with self.interface() as interface:
            out = interface.GetVoltageRangeInMicroVolt(System.UInt32(0)) / (1000)
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
            out = interface.GetNumberOfTriggerInputs()
        return out

    def stop_stimulation(self, triggerIndex: List[int] = []):
        """stops all trigger inputs or a selection based on a list 
        
        Triggers are mapped to channels according to the channelmap. By default, all triggers are mapped to channels following diagonal identity, i.e. trigger 0 maps to channel 0. This is done during initialization of the STG4000 object. Use :meth:`~STG4000.diagonalize_triggermap` to repeat this normalization.
        
        args
        ----
        channel_index:list
            defaults to all, which sets all channels to voltage mode
            otherwise, takes a list of integers of the targets, 
            e.g. [0,1]
            Indexing starts at 0.
        
        """

        if triggerIndex == []:
            triggerIndex = [c for c in range(self.channel_count)]
        with self.interface() as interface:
            interface.SendStop(System.UInt32(bitmap(triggerIndex)))

    def start_stimulation(self, triggerIndex: List[int] = []):
        """starts all trigger inputs or a selection based on a list 
        
        Triggers are mapped to channels according to the channelmap. By default, all triggers are mapped to channels following diagonal identity, i.e. trigger 0 maps to channel 0. This is done during initialization of the STG4000 object. Use :meth:`~STG4000.diagonalize_triggermap` to repeat this normalization.
        
        args
        ----
        channel_index:list
            defaults to all, which sets all channels to voltage mode
            otherwise, takes a list of integers of the targets, 
            e.g. [0,1]
            Indexing starts at 0.
        
        """

        if triggerIndex is []:
            triggerIndex = [c for c in range(self.channel_count)]
        with self.interface() as interface:
            interface.SendStart(System.UInt32(bitmap(triggerIndex)))

    def diagonalize_triggermap(self):
        """Normalize the channelmap to a diagonal
                
        Triggers are mapped to channels according to the channelmap. This is 
        done at the lower level with interface.SetupTrigger. 
        
        Use this function to normalize the mapping of trigger to channel to a diagonal identity, i.e. trigger 0 maps to channel 0,  so on.

            +----------+---+---+---+---+---+---+---+---+
            | Trigger  | 0 | 1 | 2 | 3 | 4 | 5 | 6 | 7 |
            +----------+---+---+---+---+---+---+---+---+
            | Channel  | 0 | 1 | 2 | 3 | 4 | 5 | 6 | 7 |
            +----------+---+---+---+---+---+---+---+---+
        
        """
        cmap = []
        syncmap = []
        digoutmap = []
        autostart = []
        callback_threshold = []
        for i in range(self.channel_count):
            cmap.append(System.UInt32(1 << i))
            syncmap.append(System.UInt32(1 << i))
            digoutmap.append(System.UInt32(1 << i))
            autostart.append(System.UInt32(0))  #
            callback_threshold.append(System.UInt32(50))  # 50% of buffersize
        with self.interface() as interface:
            interface.SetupTrigger(
                cmap, syncmap, digoutmap, autostart, callback_threshold
            )

    def set_samplingrate(self, rate_in_hz: int = 50000):
        """Change the output rate of the STG. 
        Valid rates are from 1000 Hz to 50000 Hz.
        """
        with self.interface() as interface:
            interface.SetOutputRate(System.UInt32(rate_in_hz))

    def set_samplingstep(self, step_in_ms: float = 0.02):
        """Change the output rate of the STG by setting the time between samples
        Valid steps are from 0.02 to 1ms
        args
        
        step_in_ms: float
            Defaults to 0.02, which corresponds to 20 µs
        """
        if step_in_ms < 0.02 or step_in_ms > 1:
            raise ValueError(
                f"Step duration is {step_in_ms}, but must be within 0.02 to 1 ms"
            )
        rate_in_hz = 1 / step_in_ms * 1000
        self.set_samplingrate(rate_in_hz)

    def send_data(self):
        with self.interface() as interface:
            for chan in range(self.channel_count):
                space = interface.GetDataQueueSpace(chan)
                while space > 1000:
                    signal = []
                    for i in range(1000):
                        sample = 30_000 * sin(2 * pi / 1000 * (chan + 1) * i)
                        signal.append(System.Int16(sample))
                    interface.EnqueueData(chan, signal)
                    space = interface.GetDataQueueSpace(chan)


# %%
self = STG4000()
interface = self.interface()
interface.connect()
interface.StartLoop()
interface.SendStart(System.UInt32(0))
for chan in range(self.channel_count):
    space = interface.GetDataQueueSpace(chan)
    while space > 1000:
        signal = []
        for i in range(1000):
            sample = 30_000 * sin(2 * pi / 1000 * (chan + 1) * i)
            signal.append(System.Int16(sample))
        interface.EnqueueData(chan, signal)
        space = interface.GetDataQueueSpace(chan)
# # %%
# info = available()[0]
# buffer_size = 50_000
# device = StreamingInterface(info, buffer_size)
# device.connect()
# device.SetCurrentMode()


# set_samplingstep(device, 0.02)
# total_memory = device.GetTotalMemory()
# nTrigger = device.GetNumberOfTriggerInputs()
# trigger_capacity = [System.UInt32(buffer_size) for i in range(nTrigger)]
# device.SetCapacity(trigger_capacity)
# cmap = []
# syncmap = []
# digoutmap = []
# autostart = []
# callback_threshold = []
# for i in range(nTrigger):
#     cmap.append(System.UInt32(1 << i))
#     syncmap.append(System.UInt32(1 << i))
#     digoutmap.append(System.UInt32(1 << i))
#     autostart.append(System.UInt32(0))  #
#     callback_threshold.append(System.UInt32(50))  # 50% of buffersize
# device.SetupTrigger(cmap, syncmap, digoutmap, autostart, callback_threshold)

# device.StartLoop()
# sleep(1)
# device.SendStart(System.UInt32(0))
# while True:
#     send_data(device)


# device.SendStop(System.UInt32(0))
# device.SendStop()
# device.StopLoop()
# device.disconnect()

