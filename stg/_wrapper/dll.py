from pathlib import Path
from sys import platform
from typing import List, Union, Any, Callable
from time import sleep
from abc import ABC, abstractmethod

# ----------------------------------------------------------------------------
# Mocking everything in case we run this for testing or on Linux
if "win" in platform:  # pragma no cover
    # pylint: disable=import-error
    import clr
    import System
    from stg.install import DLLPATH

    lib = System.Reflection.Assembly.LoadFile(str(DLLPATH))
    from Mcs.Usb import (
        CMcsUsbListNet,
        DeviceEnumNet,
        CStg200xStreamingNet,
        CStg200xDownloadNet,
        STG_DestinationEnumNet,
    )

    CURRENT = STG_DestinationEnumNet.channeldata_current
    VOLTAGE = STG_DestinationEnumNet.channeldata_voltage
    from Mcs.Usb import CMcsUsbListEntryNet as DeviceInfo
else:  # pragma no cover
    from stg._wrapper.mock import (
        CMcsUsbListNet,
        DeviceEnumNet,
        CStg200xStreamingNet,
        CStg200xDownloadNet,
        CURRENT,
        VOLTAGE,
        DeviceInfo,
    )

from stg._wrapper.mock import CStg200xMockNet

# ------------------------------------------------------------------------------
def available() -> List[DeviceInfo]:
    "list all available MCS STGs connected over USB with this PC"
    deviceList = CMcsUsbListNet()
    deviceList.Initialize(DeviceEnumNet.MCS_STG_DEVICE)
    devices = []
    for dev_num in range(0, deviceList.GetNumberOfDevices()):
        devices.append(deviceList.GetUsbListEntry(dev_num))
    return devices


def select(serialnumber: int = None) -> Union[DeviceInfo, None]:
    "select an STG with a specific serial number from all connected devices"
    deviceList = CMcsUsbListNet()
    deviceList.Initialize(DeviceEnumNet.MCS_STG_DEVICE)
    for dev_num in range(0, deviceList.GetNumberOfDevices()):
        snum = int(deviceList.GetUsbListEntry(dev_num).SerialNumber)
        if snum == serialnumber:
            device = deviceList.GetUsbListEntry(dev_num)
    return device


def bitmap(valuelist: list):
    bmap = sum(map(lambda x: 2 ** x, valuelist))
    return None if bmap == 0 else bmap


# ------------------------------------------------------------------------------
class BasicInterface(ABC):
    """Implements the `with` syntax for connecting to a CStg200xDownloadNet or CStg200xStreamingNet
    
    .. code-block:: python

       with BasicInterface() as interface:
           interface.start_stimulation()
       
    which is roughly equivalent to

    . code-block:: python

       interface = BasicInterface()
       try:
           interface.connect()
           interface.start_stimulation()
       except Exception: 
           pass
       finally:
           interface.disconnect()
    
    """

    @abstractmethod
    def __init__(self, info: DeviceInfo, *args, **kwargs):  # pragma no cover
        pass

    def connect(self) -> int:
        "connect with the device"
        self.connected = True
        return self._interface.Connect(self._info)

    def disconnect(self):
        "disconnect from the device"
        self.connected = False
        self._interface.Disconnect()

    def __enter__(self):
        err = self.connect()
        if err == 0:
            return self
        else:  # pragma no cover
            raise ConnectionRefusedError(f"{err}")

    def __exit__(self, type, value, tb):
        self.disconnect()

    def __getattr__(self, item):
        return getattr(self._interface, item)


class MockingInterface(BasicInterface):
    def __init__(self, info: DeviceInfo, *args, **kwargs):
        self.connected = False
        self._info = info
        self._interface = CStg200xMockNet(*args, **kwargs)


class DownloadInterface(BasicInterface):
    def __init__(self, info: DeviceInfo):
        self._info = info
        self._interface = CStg200xDownloadNet()


class StreamingInterface(BasicInterface):
    def __init__(self, info: DeviceInfo, buffer_sz: int = 50_000):
        self._info = info
        self._interface = CStg200xStreamingNet(System.UInt32(buffer_sz))


class STGX(ABC):
    def __init__(self, serial: int = None):
        if serial is None:
            info = available()[0]
        else:
            info = select(serial)
        print("Selecting {0:s}:SN {1:s}".format(info.DeviceName, info.SerialNumber))
        self._info = info
        self.diagonalize_triggermap()

    @abstractmethod
    def interface(self):  # pragma no cover
        return BasicInterface(None)

    def sleep(self, duration_in_ms: float):
        "sleep for duration in milliseconds"
        sleep(duration_in_ms / 1000)

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
                for chan in channel_index:
                    interface.SetCurrentMode(System.UInt32(chan))

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
                for chan in channel_index:
                    interface.SetVoltageMode(System.UInt32(chan))

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

        if triggerIndex == []:
            triggerIndex = [c for c in range(self.channel_count)]
        with self.interface() as interface:
            interface.SendStart(System.UInt32(bitmap(triggerIndex)))

    @abstractmethod
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
        pass
