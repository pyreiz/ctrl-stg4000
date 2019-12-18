from time import sleep
from typing import List
from stg._wrapper.dll import (
    System,
    CMcsUsbListNet,
    CStg200xStreamingNet,
    STG_DestinationEnumNet,
    DeviceInfo,
    available,
    select,
    bitmap,
)

