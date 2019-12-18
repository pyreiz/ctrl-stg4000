from pathlib import Path
from sys import platform
from typing import List, Union

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

    from Mcs.Usb import CMcsUsbListEntryNet as DeviceInfo
else:
    print("Mocking the STG4000 because not in Windows")

    def _mock(*args, **kwargs):
        pass

    CMcsUsbListNet = _mock
    DeviceEnumNet = _mock
    CStg200xStreamingNet = _mock
    CStg200xDownloadNet = _mock
    STG_DestinationEnumNet = _mock
    DeviceInfo = None


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
