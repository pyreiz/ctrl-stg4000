import threading
from typing import List, Dict, Callable
from stg._wrapper.dll import (
    StreamingInterface,
    CStg200xStreamingNet,
    System,
    STGX,
    DeviceInfo,
)
from stg._wrapper.downloadnet import STG4000 as STG4000DL
from stg.pulsefile import decompress
import time


def queue(device, signal: List[int], chan: int = 0):
    space = device.GetDataQueueSpace(chan)
    if space < len(signal):
        return 0
    device.EnqueueData(chan, System.Array[System.Int16](signal))
    return space - device.GetDataQueueSpace(chan)


def set_capacity(device, capacity: int):
    total_memory = device.GetTotalMemory()
    print(f"Total memory: {total_memory}")
    nTrigger = device.GetNumberOfTriggerInputs()
    max_capacity = total_memory / nTrigger
    print(f"Capacity: {capacity}/{max_capacity}")
    if capacity > max_capacity:  # pragma  no cover
        raise ValueError(
            f"Capacity {capacity} is higher than max_capacity {max_capacity}"
        )
    trigger_capacity = [System.UInt32(capacity) for i in range(nTrigger)]
    device.SetCapacity(trigger_capacity)


def diagonalize_triggermap(device, callback_percent: int = 10):
    nTrigger = device.GetNumberOfTriggerInputs()
    cmap = []
    syncmap = []
    digoutmap = []
    autostart = []
    callback_threshold = []
    for i in range(nTrigger):
        cmap.append(System.UInt32(1 << i))
        syncmap.append(System.UInt32(0 << i))  # no syncout
        digoutmap.append(System.UInt32(1 << i))
        autostart.append(System.UInt32(0))  #
        callback_threshold.append(System.UInt32(callback_percent))  # 10% of buffersize

    device.SetupTrigger(cmap, syncmap, digoutmap, autostart, callback_threshold)


class SignalMapping(dict):
    lock = threading.Lock()
    _scalar = 2_000  #: to make 1 equal to 1mA in current mode

    def __init__(self):
        super().__init__()

    def __setitem__(self, key, value):
        with self.lock:
            if type(key) != int or key < 0 or key > 7:
                raise ValueError("Key must be a possible channel from 0-7")
            value = [int(v) * self._scalar for v in value]
            super().__setitem__(key, value)

    def __getitem__(self, key) -> List[int]:
        with self.lock:
            return super().__getitem__(key)


# -----------------------------------------------------------------------------
class STG4000Streamer(STG4000DL):
    """
    This class implements the interface to stream data. 

    .. admonition:: Quote from the documentation of the DLL:


        *The Streaming mode works by use of two ring buffers which hold data. One is in PC memory and managed by the DLL, and one is in on-board STG memory. Data is transfered from PC memory to the STG via the USB bus in time slices of one millisecond.*

        *The user can define both the size of the ring buffer in DLL memory and in the STG memory. Once the Streaming mode is started, the STG request data from the PC. The data rate from PC to STG is variable and controlled by the STG. The STG request data from the PC at a rate to keep its internal ringbuffer at about half full.*

        *It is the responsibility of the user to keep the ring buffer in the memory of the PC filled, so the DLL can supply sufficient data to the STG. To do so, the Windows DLL allows to define a "callback" function which is called whenever new data is needed, or more precise, as soon as the ring buffer in the memory of the PC falls below the user defined threshold.*

        *Small buffers have the advantage of a low latency between data generation in the callback funtion and its output as a analog signal from the STG. However for low latency to work, the user-written callback function has to be fast and to produce a steady flow of data.*
        

    For you, that means you have to set two parameters carefully when you initialize the streaming mode with :meth:`~.start_streaming`. These parameters are the :code:`buffer_in_s`, which defines the size of the buffer in the DLL, and the :code:`capacity_in_s`, which defines the size of the buffer on the STG. Both buffers need to be at least as large the the signal you want to buffer. Yet, larger buffer means that the latency when updating it becomes larger, too. Too short buffers will fail without error, and too large buffers might cause 

    Streaming is implemented by constantly reading the stimulation signal you have set with :meth:`~.set_signal` for each channel, and pushing this signal into the DLL-buffer as soon as there is enough space. This is done within its own thread, and if you use :meth:`~.set_signal` it is thread-safe. Yet, space in the DLL becomes available at the speed the STG pulls data from the DLL. That means not only that there is a natural jitter, but there are also racing conditions if you update your signal faster than data is actually being pulled from the STG. 
    
    .. note::
    
       * Uncontrolled racing conditions when adapting stimulation online
       * Extensively test the optimal buffer sizes for your stimulation signal
    
    Example
    -------

    .. code-block:: python

       import time
       from stg.api import STG4000
       
       buffer_in_s=0.05 # how large is the buffer in the DLL?       
       capacity_in_s=.1 # how large is the buffer on the STG?

       stg = STG4000()
       stg.start_streaming(capacity_in_s=capacity_in_s, 
                           buffer_in_s=buffer_in_s)
       while True:
           stg.set_signal(0, amplitudes_in_mA=[0], durations_in_ms=[.1])
           time.sleep(0.5)    
           stg.set_signal(0, amplitudes_in_mA=[1, -1, 0], durations_in_ms=[.1, .1, 49.7])
           time.sleep(buffer_in_s / 2)  

    .. warning::
    
        This class inherits from :class:`~.STG4000` and therefore you can use this class also to download, start, and stop stimulation. How these two modes mix has not been tested so far. Be safe and use either or.


    """

    _streaming = threading.Event()
    _outputrate: int = 50_000
    _signals = SignalMapping()

    @property
    def output_rate_in_hz(self) -> int:
        "the rate at which the stg will send out data: Constant at 50 kHz."
        return self._outputrate

    def set_signal(
        self,
        channel_index: int = 0,
        amplitudes_in_mA: List[float,] = [0],
        durations_in_ms: List[float,] = [0],
    ):
        """sets the signal to be continually appended to the buffer
        
        args
        ----
        channel_index: int = 0
            the channel for which the new signal is to be defined
        amplitudes_in_mA: List[float,] = [0]
            a list of amplitudes in mA
        durations_in_ms: List[float,] = [0]
        a list of durations in ms


        The amplitudes and durations are decompressed (:meth:`~.stg.pulsefile.decompress`) to the sampling rate defined in :attr:`~.output_rate_in_hz`.
        
        """
        signal = decompress(
            amplitudes_in_mA=amplitudes_in_mA,
            durations_in_ms=durations_in_ms,
            rate_in_hz=self._outputrate,
        )
        self._signals[channel_index] = signal

    def streamer(self, dll_buffer_size: int = 5_000):
        return StreamingInterface(self._info, buffer_size=dll_buffer_size)

    def _stream(
        self,
        barrier: threading.Barrier,
        capacity_in_s: float = 1,
        buffer_in_s: float = 0.1,
        callback_percent: int = 10,
    ):
        rate = self.output_rate_in_hz
        capacity = int(rate * capacity_in_s)
        buffer_size = int(rate * buffer_in_s)
        with self.streamer(buffer_size) as device:
            device.SetCurrentMode()
            device.EnableContinousMode()
            set_capacity(device, capacity)
            diagonalize_triggermap(device, callback_percent)
            device.SetOutputRate(System.UInt32(rate))

            device.StartLoop()
            time.sleep(1)  # suggest by documentation for initialization of the loop
            nTrigger = device.GetNumberOfTriggerInputs()
            for i in range(nTrigger):
                device.SendStart(System.UInt32(i))
            try:
                barrier.wait()
                #               t0 = time.time()
                print("Start streaming")
                while self._streaming.is_set():
                    #                   delta = time.time() - t0
                    prg = self._signals[0].copy()
                    #                    print(delta, prg[19])
                    for chan, prg in self._signals.items():
                        sent = queue(device, signal=prg, chan=chan)
                        while not sent:
                            sent = queue(device, signal=prg, chan=chan)
                            if self._streaming.is_set() == False:
                                break

            except Exception as e:  # pragma no cover
                print(f"Exception: {e}")
            finally:
                for i in range(nTrigger):
                    device.SendStop(System.UInt32(i))
                device.StopLoop()
                device.Disconnect()

    def start_streaming(
        self,
        capacity_in_s: float = 1,
        buffer_in_s: float = 0.1,
        callback_percent: int = 10,
    ):
        """start streaming
        
        sets the STG into streaming mode and creates buffers of the respective sizes within the DLL and on the STG. After the thread has initalized, it starts pushing data as set by :meth:`~.set_signal` as soon as space is left in the DLL buffer.

        args
        ----
        capacity_in_s: float = 1
            the size of the buffer in the DLL
        buffer_in_s: float = 0.1
            the size of the buffer on the STG
        callback_percent: int = 10
            at what state of the DLL-buffer the DLL should request new data. Should have no effect in this implementation, because we constanly push data into the buffer as soon as there is enough space.
        
        """
        barrier = threading.Barrier(2)
        self._streaming.set()
        self._t = threading.Thread(
            target=self._stream,
            kwargs={
                "barrier": barrier,
                "capacity_in_s": capacity_in_s,
                "buffer_in_s": buffer_in_s,
                "callback_percent": callback_percent,
            },
        )
        self._t.start()
        barrier.wait()

    def stop_streaming(self):
        """closes the thread started when calling :meth:`~.start_streaming` gracefully
        """
        self._streaming.clear()
        if hasattr(self, "_t"):
            self._t.join()
            del self._t
