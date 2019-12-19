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


def set_capacity(device, capacity: int, channel: int = 0):
    total_memory = device.GetTotalMemory()
    nTrigger = device.GetNumberOfTriggerInputs()
    print(f"Total memory: {total_memory}")
    trigger_capacity = []
    capacity = total_memory / nTrigger
    print(f"Capacity: {capacity}")
    for i in range(nTrigger):
        if i == channel:
            trigger_capacity.append(System.UInt32(capacity))
        else:
            trigger_capacity.append(System.UInt32(1))

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

    _capacity: float = 1  # 100ms
    _dll_bufsz: int = 50_000  #: how many samples will be allocated in total across all channels
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
    def channel_capacity_in_s(self) -> float:
        return self._capacity

    @channel_capacity_in_s.setter
    def channel_capacity_in_s(self, capacity_in_s: float):
        self._capacity = capacity_in_s

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

    def _stream(self, barrier: threading.Barrier):
        with self.streamer() as device:
            device.SetCurrentMode()
            device.EnableContinousMode()
            rate = self.output_rate_in_hz
            capacity = int(rate * self.channel_capacity_in_s)
            set_capacity(device, capacity, 0)
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
                delta = 0.0
                print("Start stimulation")
                while self._streaming.is_set():
                    delta = time.time() - t0
                    prg = self._signals[0].copy()
                    print(delta, prg[19])
                    sent = queue(device, signal=prg, chan=0)
                    while not sent:
                        sent = queue(device, signal=prg, chan=0)
                        if self._streaming.is_set() == False:
                            break

            except Exception as e:  # pragma no cover
                print(f"Exception: {e}")
            finally:
                for i in range(nTrigger):
                    device.SendStop(System.UInt32(i))
                device.StopLoop()
                device.Disconnect()

    def start_streaming(self):
        barrier = threading.Barrier(2)
        self._streaming.set()
        self._t = threading.Thread(target=self._stream, kwargs={"barrier": barrier})
        self._t.start()
        barrier.wait()

    def stop_streaming(self):
        self._streaming.clear()
        if hasattr(self, "_t"):
            self._t.join()
            del self._t
