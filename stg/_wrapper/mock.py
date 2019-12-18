from typing import Any


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


CStg200xStreamingNet = CStg200xDownloadNet = CStg200xMockNet
CURRENT = 1
VOLTAGE = 0
DeviceInfo = Any


def _mock(*args, **kwargs):
    print("Mocking a call with", args, kwargs)
    pass


CMcsUsbListNet = _mock
DeviceEnumNet = _mock
STG_DestinationEnumNet = _mock

