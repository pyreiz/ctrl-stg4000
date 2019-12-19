from multiprocessing import Manager
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
from functools import lru_cache


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


class STG4000(STG4000DL):
    def _streamer(self, buffer_size: int = 100):
        return StreamingInterface(self._info, buffer_size=buffer_size)

    def stream(
        self,
        channel_index: int = 0,
        amplitudes_in_mA: List[float,] = [0],
        rate_in_hz: int = 50_000,
        mode="current",
    ):
        # maxvalue int16 32767
        # minvalue int16 -32768
        # info = available()[0]
        buffer_size = 50_000
        #  device = CStg200xStreamingNet(System.UInt32(buffer_size))
        with self._streamer(buffer_size=buffer_size) as device:
            # device.SetVoltageMode()
            device.SetCurrentMode()
            device.EnableContinousMode()
            # device.DisableContinousMode()

            rate = 50_000
            set_capacity(device, rate, 0)
            diagonalize_triggermap(device)
            device.SetOutputRate(System.UInt32(rate))

            device.StartLoop()
            time.sleep(1)
            nTrigger = device.GetNumberOfTriggerInputs()
            for i in range(nTrigger):
                device.SendStart(System.UInt32(i))

            print("Start stimulation")
            t0 = time.time()
            scalar = 2_000
            try:
                amp = 0
                while time.time() - t0 < 10:
                    amp = 1 if amp == 0 else 0
                    signal = [scalar * amp] * 5 + [scalar * -amp] * 5 + [0, 0] * 500
                    while not queue(device, signal=signal, chan=0):
                        # print(signal)
                        pass

            except Exception as e:
                print(f"Exception: {e}")

            finally:
                for i in range(nTrigger):
                    device.SendStop(System.UInt32(i))
                device.StopLoop()
                device.Disconnect()


# -----------------------------------------------------------------------------
class STG4000Streamer(STG4000DL):
    def _streamer(self, buffer_size: int = 100):
        return StreamingInterface(self._info, buffer_size=buffer_size)

    def stream(
        self,
        signal: Dict[int, List[float]],
        duration_in_s: int = 10,
        rate_in_hz: int = 50_000,
    ):
        # maxvalue int16 32767
        # minvalue int16 -32768
        # info = available()[0]
        buffer_size = 50_000
        #  device = CStg200xStreamingNet(System.UInt32(buffer_size))
        with self._streamer(buffer_size=buffer_size) as device:
            # device.SetVoltageMode()
            device.SetCurrentMode()
            device.EnableContinousMode()
            # device.DisableContinousMode()

            rate = 50_000
            set_capacity(device, rate, 0)
            diagonalize_triggermap(device)
            device.SetOutputRate(System.UInt32(rate))

            device.StartLoop()
            time.sleep(1)
            nTrigger = device.GetNumberOfTriggerInputs()
            for i in range(nTrigger):
                device.SendStart(System.UInt32(i))

            print("Start stimulation")
            t0 = time.time()
            delta = 0
            scalar = 2_000
            try:
                amp = 0
                while delta < duration_in_s:
                    delta = time.time() - t0
                    amp = 1 if amp == 0 else 0
                    prg = [scalar * s for s in signal.copy()]
                    print(delta, signal[19])
                    while not queue(device, signal=prg, chan=0):
                        # print(signal)
                        pass

            except Exception as e:
                print(f"Exception: {e}")

            finally:
                for i in range(nTrigger):
                    device.SendStop(System.UInt32(i))
                device.StopLoop()
                device.Disconnect()


# # ------------------------------------------------------------------------------
# def queue_once(device: StreamingInterface, signal: List[float], chan: int = 0):
#     space = device.GetDataQueueSpace(chan)
#     if space < len(signal):
#         return 0
#     device.EnqueueData(chan, System.Array[System.Int16](signal))
#     return space - device.GetDataQueueSpace(chan)


# def queue_forever(device):
#     # , signals: Dict[int, List[float]], running: threading.Event):
#     print("STREAMER: started queuing forever")
#     # while running.is_set():
#     #     for chan, signal in signals.items():
#     #         while not queue_once(device, signal=signal, chan=chan):
#     #             if not running.is_set():
#     #                 break
#     with device() as device:
#         # device.SetVoltageMode()
#         device.SetCurrentMode()
#         device.EnableContinousMode()
#         # device.DisableContinousMode()

#         rate = 50_000
#         set_capacity(device, rate, 0)
#         diagonalize_triggermap(device)
#         device.SetOutputRate(System.UInt32(rate))

#         device.StartLoop()
#         time.sleep(1)
#         nTrigger = device.GetNumberOfTriggerInputs()
#         for i in range(nTrigger):
#             device.SendStart(System.UInt32(i))

#         print("Start stimulation")
#         t0 = time.time()
#         scalar = 2_000
#         try:
#             amp = 0
#             while time.time() - t0 < 10:
#                 amp = 1 if amp == 0 else 0
#                 signal = [scalar * amp] * 5 + [scalar * -amp] * 5 + [0, 0] * 500
#                 while not queue(device, signal=signal, chan=0):
#                     # print(signal)
#                     pass

#         except Exception as e:
#             print(f"Exception: {e}")

#         finally:
#             for i in range(nTrigger):
#                 device.SendStop(System.UInt32(i))
#             device.StopLoop()
#             device.Disconnect()
#     print("STREAMER: stopped queuing forever")


# def get_cached(
#     info: DeviceInfo, buffer_size: int = 100, cache=dict()
# ) -> StreamingInterface:
#     try:
#         dev = cache[(info, buffer_size)]
#         print("Found one")
#     except KeyError:
#         dev = StreamingInterface(info, buffer_size=buffer_size)
#         cache[(info, buffer_size)] = dev
#     return dev


# class STG4000Streamer(STGX):

#     _dll_bufsz: int = 100
#     _outputrate: int = 50
#     _manager = Manager()
#     _signals: Dict[int, List[float]] = _manager.dict()
#     _is_streaming: threading.Event = threading.Event()
#     _scalar = 2_000

#     def _streamer(self) -> StreamingInterface:
#         # return get_cached(info=self._info, buffer_size=self._dll_bufsz)
#         return StreamingInterface(self._info, buffer_size=self._dll_bufsz)

#     @property
#     def buffer_size(self) -> int:
#         "the size of the ring-buffer managed by the dll"
#         return self._dll_bufsz

#     @buffer_size.setter
#     def buffer_size(self, buffer_size: int = 100):
#         self._dll_bufsz = buffer_size

#     @property
#     def output_rate_in_khz(self) -> int:
#         "the rate at which the stg will send out data: Constant at 50 kHz."
#         return self._outputrate

#     def diagonalize_triggermap(self):
#         with self._streamer() as interface:
#             diagonalize_triggermap(interface)

#     @property
#     def is_streaming(self) -> bool:
#         return self._is_streaming.is_set()

#     def get_signals(self) -> Dict[int, List[float]]:
#         "get a dictionary of the currently buffered signal templates"
#         # pylint: disable=no-member
#         return self._signals.copy()

#     def set_signal(
#         self,
#         channel_index: int = 0,
#         amplitudes_in_mA: List[float,] = [0],
#         durations_in_ms: List[float,] = [0],
#     ):
#         "set one of the signal templates with decompressed amps/durs"
#         signal = decompress(
#             amplitudes_in_mA=amplitudes_in_mA,
#             durations_in_ms=durations_in_ms,
#             rate_in_khz=self._outputrate,
#         )
#         # pylint: disable=unsupported-assignment-operation
#         self._signals[channel_index] = [s * self._scalar for s in signal]

#     def start(self, mode="current"):
#         "stop streaming the signal templates"
#         self._is_streaming.set()
#         self.diagonalize_triggermap()
#         t = threading.Thread(
#             target=queue_forever,
#             args=(self._streamer, self._signals, self._is_streaming),
#         )
#         # self._streamer().connect()
#         # rate = int(self._outputrate * 1000)
#         # print("Rate is", rate)
#         # device = self._streamer()
#         # device.connect()
#         # device.SetCurrentMode()
#         # device.EnableContinousMode()
#         # set_capacity(device, rate, 0)
#         # device.SetOutputRate(System.UInt32(rate))

#         # device.StartLoop()
#         # time.sleep(1)
#         # nTrigger = device.GetNumberOfTriggerInputs()
#         # for i in range(nTrigger):
#         #     device.SendStart(System.UInt32(i))

#         print("Start stimulation")
#         t.start()

#     def stop(self):
#         "stop streaming the signal templates"
#         self._is_streaming.clear()
#         # device = self._streamer()
#         # nTrigger = device.GetNumberOfTriggerInputs()
#         # for i in range(nTrigger):
#         #     device.SendStop(System.UInt32(i))
#         # device.StopLoop()
#         # device.Disconnect()
#         # device.disconnect()

