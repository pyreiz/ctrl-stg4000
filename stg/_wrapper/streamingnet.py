from typing import List
from stg._wrapper.dll import StreamingInterface, CStg200xStreamingNet, System
from stg._wrapper.downloadnet import STG4000 as STG4000DL
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
    for i in range(nTrigger):
        if i == channel:
            trigger_capacity.append(System.UInt32(capacity))
        else:
            trigger_capacity.append(System.UInt32(1))

    device.SetCapacity(trigger_capacity)


def diagonalize_triggermap(device):
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
        callback_threshold.append(System.UInt32(10))  # 10% of buffersize

    device.SetupTrigger(cmap, syncmap, digoutmap, autostart, callback_threshold)


class STG4000(STG4000DL):
    @staticmethod
    def queue(device, amplitudes: List[float], chan: int = 0):
        space = device.GetDataQueueSpace(chan)
        if space < len(amplitudes):
            return 0
        device.EnqueueData(chan, System.Array[System.Int16](amplitudes))
        # device.EnqueueData(chan, amplitudes)
        return space - device.GetDataQueueSpace(chan)

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
                        pass

            except Exception as e:
                print(f"Exception: {e}")

            finally:
                for i in range(nTrigger):
                    device.SendStop(System.UInt32(i))
                device.StopLoop()
                device.Disconnect()

