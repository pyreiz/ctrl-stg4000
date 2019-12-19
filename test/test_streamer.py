from stg._wrapper.streamingnet import STG4000Streamer, SignalMapping
import pytest
import threading
import time


def test_signal_mapping():
    s = SignalMapping()
    with pytest.raises(ValueError):
        s[-1] = []
    with pytest.raises(ValueError):
        s[8] = []
    s[0] = [1, -1, 0]
    assert s[0] == [2000, -2000, 0]  # due to the scalar


@pytest.fixture(scope="module")
def stg():
    stg = STG4000Streamer()
    assert stg.output_rate_in_hz == 50_000
    assert stg.buffer_size == 50_000
    stg.set_signal(
        channel_index=0, amplitudes_in_mA=[1, -1, 0], durations_in_ms=[0.1, 0.1, 49.8]
    )
    assert len(stg._signals[0]) == 2500
    assert stg._signals[0][0] == 2000  # because of the scaler
    yield stg


def test_properties(stg):
    stg.buffer_size = 99
    assert stg.buffer_size == 99


def test_start_stop():
    duration = 5.0
    stg = STG4000Streamer()

    stg.set_signal(0, amplitudes_in_mA=[1, -1, 0], durations_in_ms=[0.1, 0.1, 49.8])
    # t = threading.Thread(target=stg.stream, kwargs={"duration_in_s": duration})

    # t.start()
    stg.start_streaming(duration_in_s=duration)
    t0 = time.time()
    flipped = False
    while True:
        if time.time() - t0 > 2.5 and not flipped:
            flipped = True
            print("Switch the signal")
            stg.set_signal(
                0, amplitudes_in_mA=[1, -1, 0], durations_in_ms=[0.2, 0.2, 49.6]
            )
        if time.time() - t0 > duration:
            break
        time.sleep(0.01)
    stg.stop_streaming()

