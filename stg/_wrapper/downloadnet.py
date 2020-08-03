# -*- coding: utf-8 -*-
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
    """
    This class implements the interface to download, start and stop stimulation. 

    At this point, you should pay attention to two specific details. First, indexing starts at 0. That means, the first channel is channel 0. Second, there is a difference between channels and triggers for the STG. Triggers are mapped to channels according to a channelmap. That means a single trigger can start stimulation of a whole set of channels. During initialization of the STG, we give this a sensible default. That means, all triggers are mapped to the respective channels following diagonal identity, i.e. trigger 0 maps to channel 0. Use :meth:`~STG4000.diagonalize_triggermap` to repeat this normalization.


    Example
    -------

    .. code-block:: python

        import time
        from stg.api import STG4000
        
        stg = STG4000()
        stg.download(0,[1,-1, 0], [0.1, 0.1, 49.8])
        while True:
            time.sleep(0.5)    
            a.trigger()
            stg.start_stimulation([0])

    .. note::
       
       * Indexing starts at zero
       * Differentiate triggers and channels

    .. warning::
        
       Please note, that in download mode, the Python object and the STG do not share states. More specifically, once a program is downloaded to the STG, it stays downloaded, even if you delete the object, instantiate a new one or reboot the PC. You can enforce a clean state by rebooting the STG or explicitly downloading and thereby overwriting the channels after instantiation. This behavior was kept for three reasons. First, this is also the behavior of the MCS GUI, and therefore less non-intuitive if you come from this direction. Second, it clearly shows that in download mode, PC and STG are not coupled, i.e. once downloaded, you can trigger without any USB connection. Third, clearing the downloaded programs during instantiation (or deletion of the object) would prevent the user from common use cases like recovering the STG after a restart of the kernel, deletion of the object or unplugging the USB cable. 

    """

    def stop_stimulation(self, triggerIndex: List[int] = []):
        """stops all trigger inputs or a selection based on a list 
        
        args
        ----
        triggerIndex:List[int]
            defaults to [], which stops stimulation at all channels. Give it a list of integers to start a specific subset of triggers, e.g. [0,1].   
        
        """

        if triggerIndex == []:
            triggerIndex = [c for c in range(self.channel_count)]
        with self.interface() as interface:
            interface.SendStop(System.UInt32(bitmap(triggerIndex)))

    def start_stimulation(self, triggerIndex: List[int] = []):
        """starts all trigger inputs or a selection based on a list 
        
        args
        ----
        triggerIndex:List[int]
            defaults to [], which starts stimulation at all channels. Give it a list of integers to start a specific subset of triggers, e.g. [0,1].         
        
        """

        if triggerIndex == []:
            triggerIndex = [c for c in range(self.channel_count)]
        with self.interface() as interface:
            interface.SendStart(System.UInt32(bitmap(triggerIndex)))

    def set_mode(self, channel_index: List[int] = [], mode: str = "current") -> int:
        """set a single or all channels to voltage or current mode
        
        args
        ----
        channel_index: list        
            defaults to [], which sets the mode at all channels. Give it a list of integers to set the mode only for a specific subset of channels, e.g. [0,1].
        mode: str ("current", "voltage")
            defaults to current


        .. warning::
           
           Because we primarily use current-mode, voltage mode is relatively untested. Additionally, i so far have not tested the behavior when different channels are in different modes. Be safe, and just set all channels to current-mode with :code:`stg.set_mode("current")`
        

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
        """Give each trigger a sensible channel
                       
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
            
           stg.download(channel_index = 0,
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
