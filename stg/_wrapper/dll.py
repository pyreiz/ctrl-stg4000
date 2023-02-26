from pathlib import Path
from sys import platform
from typing import List, Union, Any, Callable
from time import sleep
from abc import ABC, abstractmethod

OptionalInt = Union[int, None]

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
        System,
    )
from stg._wrapper.mock import CStg200xMockNet
from stg._wrapper.mock import info as mockinfo

# ------------------------------------------------------------------------------
def available() -> List[DeviceInfo]:
    "list all available MCS STGs connected over USB with this PC"
    deviceList = CMcsUsbListNet()
    deviceList.Initialize(DeviceEnumNet.MCS_STG_DEVICE)
    devices = []
    for dev_num in range(0, deviceList.GetNumberOfDevices()):
        devices.append(deviceList.GetUsbListEntry(dev_num))
    return devices


def select(serialnumber: OptionalInt = None) -> Union[DeviceInfo, None]:
    "select an STG with a specific serial number from all connected devices"
    if serialnumber == -1:
        return mockinfo

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
    def __init__(self, info: DeviceInfo, buffer_size: int = 50_000):
        self._info = info
        self._interface = CStg200xStreamingNet(System.UInt32(buffer_size))


class STGX(ABC):
    """
    The STGX is the base class for the STG4000 and wraps the basic USB interface and reads all the properties that are determined by the specific STG connected to your PC. Additionally methods for downloading or streaming are implemented by subclasses. Ideally, just use :code:`from stg.api import STG4000`, and you will get the class implementing all bells and whistles.

    When initialized without arguments, i.e. :code:`stg = STG4000()`, it looks through your USB ports and connects with the first STGs it finds. If you want to use a specific STG, initialize the class with the serial number of the device, e.g. using :code:`stg = STG4000(serial=12345)`.

    Immediatly after the connection is established, we eagerly read all properties from the stimulator, e.g. the number of channels or the output resolution. This read-only properties are than cached, to prevent any later overhead. This means it might take a few seconds until the :code:`stg` is initialized, but it saves you precious milliseconds when you later stimulate.

    Because at any time, only one process can be connected with a specific STG the connection is implemented using a :code:`with ... as` idiom. This should therefore be relatively safe. It is still possible that the STG can get into a weird state. In that case, try turning it off and on again.

    .. note::

        * Properties are eagerly loaded and cached during initalization
    """

    def __init__(self, serial: OptionalInt = None):
        if serial is None:
            try:
                info = available()[0]
            except IndexError as e:  # pragma no cover
                raise ConnectionError(
                    "No STG connected, or connected but not switched on."
                )
        else:  # pragma no cover
            info = select(serial)
        print(
            "Selecting {0:s}:SN {1:s}".format(
                info.DeviceName, info.SerialNumber
            )
        )
        self._info = info
        self._collect_properties()
        self.diagonalize_triggermap()

    def _collect_properties(self):
        self._str = self._info.ToString()
        self._name = self._info.DeviceName
        self._manufacturer = self._info.Manufacturer
        with self.interface() as interface:
            _, soft, hard = interface.GetStgVersionInfo("", "")
            self._version = (soft, hard)
            self._serial_number = int(self._info.SerialNumber)
            self._crinua = (
                interface.GetCurrentResolutionInNanoAmp(System.UInt32(0))
                / 1000
            )
            self._crinma = interface.GetCurrentResolutionInNanoAmp(
                System.UInt32(0)
            ) / (1000 * 1000)
            self._crngma = interface.GetCurrentRangeInNanoAmp(
                System.UInt32(0)
            ) / (1000 * 1000)
            self._crngua = interface.GetCurrentRangeInNanoAmp(
                System.UInt32(0)
            ) / (1000)
            self._vinuv = interface.GetVoltageResolutionInMicroVolt(
                System.UInt32(0)
            )
            self._vrnguv = interface.GetVoltageRangeInMicroVolt(
                System.UInt32(0)
            ) / (1000)
            self._dacr = interface.GetDACResolution()
            self._achancnt = interface.GetNumberOfAnalogChannels()
            self._trgincnt = interface.GetNumberOfTriggerInputs()

    @abstractmethod
    def diagonalize_triggermap(self):  # pragma no cover
        pass

    def interface(self):  # pragma no cover
        return DownloadInterface(self._info)

    def sleep(self, duration_in_ms: float):
        "sleep for duration in milliseconds"
        sleep(duration_in_ms / 1000)

    @property
    def name(self) -> str:
        "returns the model name, i.e. STG4002/4/8"
        return self._name

    @property
    def version(self) -> str:
        "Returns the current hardware and software version"
        soft, hard = self._version
        return "Hardware - {0} : Software - Version: {1}".format(
            hard.replace("Rev.", "Revision"), soft
        )

    @property
    def serial_number(self) -> int:
        "Returns the serial number of the device"
        return self._serial_number

    @property
    def manufacturer(self) -> str:
        "Returns the name of the manufacturer"
        return self._manufacturer

    @property
    def current_resolution_in_uA(self) -> float:
        "Return the current resolution in µA"
        return self._crinua

    @property
    def current_resolution_in_mA(self) -> float:
        "Return the current resolution in mA"
        return self._crinma

    @property
    def current_range_in_mA(self) -> float:
        "Return the current range in mA"
        return self._crngma

    @property
    def current_range_in_uA(self) -> float:
        "Return the current range in uA"
        return self._crngua

    @property
    def voltage_resolution_in_uV(self) -> float:
        "Return the voltage resolution in µV"
        return self._vinuv

    @property
    def voltage_range_in_uV(self) -> float:
        "Return the voltage range in uV"
        return self._vrnguv

    @property
    def time_resolution_in_us(self) -> float:
        "Return the time resolution in µs"
        return 20

    @property
    def time_resolution_in_ms(self) -> float:
        "Return the time resolution in ms"
        return 0.02

    @property
    def DAC_resolution(self) -> int:
        "Return the DAC resolution in bits"
        return self._dacr

    @property
    def channel_count(self) -> int:
        "returns the number of stimulation channels"
        return self._achancnt

    @property
    def trigin_count(self) -> int:
        "returns the number of  trigger inputs"
        return self._trgincnt

    def __repr__(self) -> str:
        return f"{str(self)} at {hex(id(self))}"

    def __str__(self) -> str:
        return self._str

    def _set_current_mode(self, channel_index: List[int] = []):
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

    def _set_voltage_mode(self, channel_index: List[int] = []):
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
