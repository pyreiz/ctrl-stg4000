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
    assert stg.buffer_size == 5_000
    stg.set_signal(
        channel_index=0, amplitudes_in_mA=[1, -1, 0], durations_in_ms=[0.1, 0.1, 49.8]
    )
    assert len(stg._signals[0]) == 2500
    assert stg._signals[0][0] == 2000  # because of the scaler
    yield stg


def test_properties(stg):
    stg.buffer_size = 99
    assert stg.buffer_size == 99


def test_increase_pulse_width():
    "start streaming a biphasic pulse, after 5s, increase the pulse-width"
    stg = STG4000Streamer()
    stg.set_signal(0, amplitudes_in_mA=[1, -1, 0], durations_in_ms=[0.1, 0.1, 49.8])
    stg.start_streaming(capacity_in_s=0.1)
    t0 = time.time()
    flipped = False

    while time.time() - t0 < 10:
        if time.time() - t0 > 5 and not flipped:
            flipped = True
            print("Switch the signal")
            print("\a")
            stg.set_signal(
                0, amplitudes_in_mA=[1, -1, 0], durations_in_ms=[0.2, 0.2, 49.6]
            )
        time.sleep(0.01)

    stg.stop_streaming()

