from typing import List
from stg._wrapper.dll import (
    System,
    CURRENT,
    VOLTAGE,
    available,
    select,
    DeviceInfo,
    StreamingInterface,
    CStg200xStreamingNet,
    bitmap,
    STGX,
)

import time


def queue(device, signal: List[int], chan: int = 0):
    space = device.GetDataQueueSpace(chan)
    if space < len(signal):
        return 0
    device.EnqueueData(chan, System.Array[System.Int16](signal))
    return space - device.GetDataQueueSpace(chan)


def connect(device, info):
    err = device.Connect(info)
    if err != 0:
        raise ConnectionError(
            "Error {0:f} for {1:s}:SN {2:s}".format(
                err, info.DeviceName, info.SerialNumber
            )
        )
    else:
        print(
            "Connected successfully with {0:s}:SN {1:s}".format(
                info.DeviceName, info.SerialNumber
            )
        )
    return device.GetNumberOfTriggerInputs()


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


class STG4000(STGX):
    @staticmethod
    def queue(device, amplitudes: List[float], chan: int = 0):
        space = device.GetDataQueueSpace(chan)
        if space < len(amplitudes):
            return 0
        device.EnqueueData(chan, System.Array[System.Int16](amplitudes))
        # device.EnqueueData(chan, amplitudes)
        return space - device.GetDataQueueSpace(chan)

    def interface(self, buffer_size: int = 100):
        return StreamingInterface(self._info, buffer_size=buffer_size)

    def diagonalize_triggermap(self):
        pass

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
        with self.interface(buffer_size=buffer_size) as device:
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
                for i in range(nTrigger):
                    device.SendStop(System.UInt32(i))

                device.StopLoop()
                device.Disconnect()


# -----------------------------------------------------------------------------
class OLD_STG4000(STGX):
    @staticmethod
    def queue(device, amplitudes: List[float], chan: int = 0):
        space = device.GetDataQueueSpace(chan)
        if space < len(amplitudes):
            return 0
        device.EnqueueData(chan, System.Array[System.Int16](amplitudes))
        # device.EnqueueData(chan, amplitudes)
        return space - device.GetDataQueueSpace(chan)

    def interface(self):
        return StreamingInterface(self._info)

    def diagonalize_triggermap(self):
        pass

    def stream(
        self,
        channel_index: int = 0,
        amplitudes_in_mA: List[float,] = [0],
        rate_in_hz: int = 50_000,
        mode="current",
    ):
        # maxvalue int16 32767
        # minvalue int16 -32768
        info = available()[0]
        buffer_size = 50_000
        device = CStg200xStreamingNet(System.UInt32(buffer_size))
        nTrigger = connect(device, info)

        # device.SetVoltageMode()
        device.SetCurrentMode()
        device.EnableContinousMode()
        # device.DisableContinousMode()

        rate = 50_000
        set_capacity(device, rate, 0)
        device.SetOutputRate(System.UInt32(rate))

        device.StartLoop()
        time.sleep(1)
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
            for i in range(nTrigger):
                device.SendStop(System.UInt32(i))

            device.StopLoop()
            device.Disconnect()
