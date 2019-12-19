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

    def set_mode(self, channel_index: List[int] = [], mode: str = "current") -> int:
        """set a single or all channels to voltage or current mode
        
        args
        ----
        channel_index:list
            defaults to all, which sets all channels to current mode
            otherwise, takes an integer of the target channel.
            Indexing starts at 0.    
        mode: str {"current", "voltage"}    
            defaults to current
        """
        if mode == "current":
            self._set_current_mode(channel_index)
            return CURRENT
        elif mode == "voltage":
            self._set_voltage_mode(channel_index)
            return VOLTAGE
        else:  # pragma no cover
            raise ValueError(
                f"Unknow mode {mode}. select either 'current' or ' 'voltage'"
            )

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
        channelmap = []
        syncoutmap = []
        repeat = []
        for chan_idx in range(0, self.channel_count):
            repeat.append(1)  # every trigger only once
            syncoutmap.append(1 << chan_idx)  # diagonal triggerout
            channelmap.append(1 << chan_idx)  # diagonal triggerin
        with self.interface() as interface:
            interface.SetupTrigger(0, channelmap, syncoutmap, repeat)

    def download(
        self,
        channel_index: int = 0,
        amplitudes_in_mA: List[float,] = [0],
        durations_in_ms: List[float,] = [0],
        mode="current",
    ):

        """Download a stimulation signal 
        
        .. Warning::

           Any previous data sent to that channel is erased. Other channels stay untouched.
           
        The signal is compressed as amplitudes and their respective durations 

        args
        ----
        channel_index: int
            The index of the channel for which to download the signal. Indexing
            starts at 0
        amplitudes_in_mA: List[float]
            a list of amplitudes in mA/mV delivered for the corresponding duration 
        durations_in_ms: List[float]
            a list of durations in ms determing how long each corresponding 
            amplitude is delivered
        mode: str
            defaults to current

        Example
        -------
     
        .. code-block:: python
            
           mcs.download(channel_index = 0,
                        amplitudes_in_mA = [1, -1, 0],
                        durations_in_ms = [.1, .1, .488])
           
    
        """
        if len(amplitudes_in_mA) != len(durations_in_ms):
            raise ValueError("Every amplitude needs a duration and vice versa!")

        amplitudes = [System.Int32(a * 1000_000) for a in amplitudes_in_mA]
        durations = [System.UInt64(s * 1000) for s in durations_in_ms]

        MODE = self.set_mode([channel_index], mode)
        with self.interface() as interface:
            interface.PrepareAndSendData(
                System.UInt32(channel_index), amplitudes, durations, MODE
            )
