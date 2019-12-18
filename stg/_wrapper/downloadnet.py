# -*- coding: utf-8 -*-
from typing import List
from stg._wrapper.dll import (
    System,
    CURRENT,
    VOLTAGE,
    available,
    select,
    DeviceInfo,
    DownloadInterface,
    bitmap,
    STGX,
)


class STG4000(STGX):
    def interface(self):
        return DownloadInterface(self._info)

    def download(
        self,
        channel_index: int = 0,
        amplitudes_in_mA: List[float,] = [0],
        durations_in_ms: List[float,] = [0],
    ):

        """Download a stimulation signal 
        
        The signal is compressed to amplitudes and their respective durations 
        
        args
        ----
        
        channel_index:int
            The index of the channel for which to download the signal. Indexing
            starts at 0
        amplitude:List[float,]
            a list of amplitudes in mA/mV delivered for the corresponding duration 
        duration:List[float,]
            a list of durations in ms determing how long each corresponding 
            amplitude is delivered

        .. example::
            
             mcs.download(channel_index = 0,
                          amplitude = [1, -1, 0],
                          duration = [.1, .1, .488])
             sets the first channel to a biphasic pulse with 100µs duration
             each and an amplitude of 1000µA, i.e 1mA.
        
        notes:
           The signal is downloaded with  interface.PrepareAndSendData, 
           therefore previous data sent to that channel is erased first.
        """

        amplitudes = [int(a * 1000_000) for a in amplitudes_in_mA]
        durations = [int(s * 1000) for s in durations_in_ms]
        self._download([channel_index], amplitudes, durations, "current")

    def _download(
        self,
        channel_index: List[int] = [0],
        amplitudes: List[int] = [0],
        durations: list = [20],
        mode="current",
    ):

        if len(amplitudes) != len(durations):
            raise ValueError("Every amplitude needs a duration and vice versa!")
        amplitudes = [System.Int32(a) for a in amplitudes]
        durations = [System.UInt64(d) for d in durations]

        if mode == "current":
            self.set_current_mode(channel_index)
            with self.interface() as interface:
                for chan in channel_index:
                    interface.PrepareAndSendData(chan, amplitudes, durations, CURRENT)
        elif mode == "voltage":
            self.set_voltage_mode(channel_index)
            with self.interface() as interface:
                for chan in channel_index:
                    interface.PrepareAndSendData(chan, amplitudes, durations, VOLTAGE)

