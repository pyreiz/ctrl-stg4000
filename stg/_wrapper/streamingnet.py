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

    _dll_bufsz: int = 5_000  #: how many samples will be allocated in total across all channels (10 % of outputrate -> 100 ms)
    _streaming = threading.Event()
    _outputrate: int = 50_000
    _signals = SignalMapping()

    @property
    def buffer_size(self) -> int:
        "the size of the ring-buffer managed by the dll"
        return self._dll_bufsz

    @buffer_size.setter
    def buffer_size(self, buffer_size: int = 50_000):
        self._dll_bufsz = buffer_size

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
        "set one of the signal templates with decompressed amps/durs"
        signal = decompress(
            amplitudes_in_mA=amplitudes_in_mA,
            durations_in_ms=durations_in_ms,
            rate_in_hz=self._outputrate,
        )
        self._signals[channel_index] = signal

    def streamer(self):
        return StreamingInterface(self._info, buffer_size=self.buffer_size)

    def _stream(self, barrier: threading.Barrier, capacity_in_s: float = 1):
        with self.streamer() as device:
            device.SetCurrentMode()
            device.EnableContinousMode()
            rate = self.output_rate_in_hz
            capacity = int(rate * capacity_in_s)
            set_capacity(device, capacity)
            diagonalize_triggermap(device)
            device.SetOutputRate(System.UInt32(rate))

            device.StartLoop()
            time.sleep(1)  # suggest by documentation for initialization of the loop
            nTrigger = device.GetNumberOfTriggerInputs()
            for i in range(nTrigger):
                device.SendStart(System.UInt32(i))
            try:
                barrier.wait()
                t0 = time.time()
                print("Start streaming updating with a latency of ")
                while self._streaming.is_set():
                    delta = time.time() - t0
                    prg = self._signals[0].copy()
                    print(delta, prg[19])
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

    def start_streaming(self, capacity_in_s: float = 1):
        barrier = threading.Barrier(2)
        self._streaming.set()
        self._t = threading.Thread(
            target=self._stream,
            kwargs={"barrier": barrier, "capacity_in_s": capacity_in_s},
        )
        self._t.start()
        barrier.wait()

    def stop_streaming(self):
        self._streaming.clear()
        if hasattr(self, "_t"):
            self._t.join()
            del self._t
