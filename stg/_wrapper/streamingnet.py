from typing import List
from stg._wrapper.dll import (
    System,
    CURRENT,
    VOLTAGE,
    available,
    select,
    DeviceInfo,
    StreamingInterface,
    bitmap,
    STGX,
)


class STG4000(STGX):
    def interface(self):
        return DownloadInterface(self._info)

    def stream(
        self,
        channel_index: int = 0,
        amplitudes_in_mA: List[float,] = [0],
        durations_in_ms: List[float,] = [0],
        mode="current",
    ):
        """
        
        args
        ----
        channel_index:int
            The index of the channel for which to download the signal. Indexing
            starts at 0
        amplitudes_in_mA:List[float,]
            a list of amplitudes in mA/mV delivered for the corresponding duration 
        rate_in_hz: int
            the rate at which the entries in the amplitudes are delivered
        mode: str {"current", "voltage"}
            defaults to current

        .. example::
            
             stg.queue(channel_index = 0,
                        amplitudes_in_mA = [1, -1, 0],)   

        """
        amplitudes = [System.Int32(a * 1000_000) for a in amplitudes_in_mA]
