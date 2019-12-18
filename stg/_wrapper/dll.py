from pathlib import Path
from sys import platform
from typing import List, Union, Any

# ----------------------------------------------------------------------------
# Mocking everything in case we run this for testing or on Linux
if "win" in platform:
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
else:
    from stg._wrapper.mock import (
        CMcsUsbListNet,
        DeviceEnumNet,
        CStg200xStreamingNet,
        CStg200xDownloadNet,
        CURRENT,
        VOLTAGE,
    )


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
class BasicInterface:
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

    def __init__(self, info: DeviceInfo, *args, **kwargs):
        self.connected = False
        self._info = info
        self._interface = CStg200xMockNet(*args, **kwargs)

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
        else:
            raise ConnectionRefusedError(f"{err}")

    def __exit__(self, type, value, tb):
        self.disconnect()

    def __getattr__(self, item):
        return getattr(self._interface, item)


class DownloadInterface(BasicInterface):
    def __init__(self, info: DeviceInfo):
        self._info = info
        self._interface = CStg200xDownloadNet()


class StreamingInterface(BasicInterface):
    def __init__(self, info: DeviceInfo, buffer_sz: int = 50_000):
        self._info = info
        self._interface = CStg200xStreamingNet(System.UInt32(buffer_sz))
