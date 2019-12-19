from typing import Any


def _mock(*args, **kwargs):
    print("Mocking a call with", args, kwargs)
    pass


def transit(x):
    return x


from unittest.mock import Mock, PropertyMock
from unittest.mock import MagicMock

DeviceInfo = MagicMock()
DeviceInfo.DeviceName = "STGmock"
DeviceInfo.SerialNumber = "1007"
DeviceInfo.ToString = MagicMock(return_value="Mock")
DeviceList = MagicMock()
DeviceList.GetNumberOfDevices = MagicMock(return_value=1)
DeviceList.GetUsbListEntry = MagicMock(return_value=DeviceInfo)
CMcsUsbListNet = MagicMock(return_value=DeviceList)
DeviceEnumNet = Mock()
DeviceEnumNet.MCS_STG_DEVICE = None
STG_DestinationEnumNet = _mock


System = MagicMock()
System.UInt32 = int
System.Int16 = int
System.Array = list


def DataQueueSpace():
    while True:
        yield from [100, 1000, 2000]


class CStg200xMockNet:
    """Mock a CStg200xDownloadNet or CStg200xStreamingNet for testing and development
    
    """

    def __init__(self, *args, **kwargs):
        pass

    def Connect(self, info: Any) -> int:
        """Open a connection to the device. 

        args
        ----
        info:DeviceInfo
            The DeviceInfo for the device to be connected. 

        returns
        -------
        error: int
            Error Status. 0 on success.
        """
        print("MOCK:CONNECT with a MOCK STG")
        return 0

    def Disconnect(self) -> None:
        "Disconnect from a device."
        print("MOCK:DISCONNECT from a MOCK STG")
        pass

    def GetCurrentResolutionInNanoAmp(self, ptr) -> int:
        return 1

    def GetCurrentRangeInNanoAmp(self, ptr) -> int:
        return 1

    def GetVoltageResolutionInMicroVolt(self, ptr) -> int:
        return 1

    def GetVoltageRangeInMicroVolt(self, ptr) -> int:
        return 1

    def GetDACResolution(self) -> int:
        return 1

    def GetNumberOfAnalogChannels(self):
        return 2

    def SetupTrigger(self, *args, **kwargs):
        pass

    def GetStgVersionInfo(self, a: str, b: str):
        return "ignore", "M-Soft", "M-Hard"

    def EnableContinousMode(self, *args, **kwargs):
        pass

    def SetCurrentMode(self, *args, **kwargs):
        pass

    def SetVoltageMode(self, *args, **kwargs):
        pass

    def SendStart(self, bmap):
        pass

    def SendStop(self, bmap):
        pass

    def GetTotalMemory(self):
        return 10000

    def GetNumberOfTriggerInputs(self):
        return 2

    def SetCapacity(self, *args, **kwargs):
        pass

    def SetOutputRate(self, *args, **kwargs):
        pass

    def StartLoop(self):
        pass

    def EnqueueData(self, *args, **kwargs):
        pass

    def StopLoop(self):
        pass

    def PrepareAndSendData(self, *args, **kwargs):
        pass

    DataQueueSpace = DataQueueSpace()

    def GetDataQueueSpace(self, *args, **kwargs):
        return next(self.DataQueueSpace)


CStg200xStreamingNet = CStg200xDownloadNet = CStg200xMockNet
CURRENT = 1
VOLTAGE = 0
DeviceInfo = Any
