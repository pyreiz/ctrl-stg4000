from stg._wrapper.streamingnet import STG4000Streamer
import pytest
import threading
import time

# @pytest.fixture(scope="module")
# def stg():
#     stg = STG4000Streamer()
#     assert stg.output_rate_in_khz == 50
#     assert list(stg.get_signals().keys()) == []
#     assert stg.buffer_size == 100
#     stg.set_signal(
#         channel_index=0, amplitudes_in_mA=[1, -1, 0], durations_in_ms=[0.1, 0.1, 49.8]
#     )
#     yield stg


# def test_properties(stg):
#     stg.buffer_size = 99
#     assert stg.buffer_size == 99


def test_start_stop():
    stg = STG4000Streamer()
    from multiprocessing import Manager

    manager = Manager()
    signal = manager.list()
    signal = [1] * 5 + [-1] * 5 + [0] * 1000
    duration = 20
    t = threading.Thread(
        target=stg.stream, args=(signal,), kwargs={"duration_in_s": duration}
    )

    t.start()
    t0 = time.time()
    flipped = False
    while True:
        if time.time() - t0 > 10 and not flipped:
            flipped = True
            print("Switched the signal")
            _signal = [1] * 10 + [-1] * 10
            signal[0:20] = _signal[0:20]
        if time.time() - t0 > duration:
            t.join()
            break
        time.sleep(0.01)

