from stg._wrapper.streamingnet import STG4000Streamer
import pytest


@pytest.fixture(scope="module")
def stg():
    stg = STG4000Streamer()
    assert stg.output_rate_in_khz == 50
    assert list(stg.get_signals().keys()) == []
    assert stg.buffer_size == 100
    stg.set_signal(
        channel_index=0, amplitudes_in_mA=[1, -1, 0], durations_in_ms=[0.1, 0.1, 49.8]
    )
    yield stg


def test_properties(stg):
    stg.buffer_size = 99
    assert stg.buffer_size == 99


def test_start_stop(stg):
    stg.set_signal(
        channel_index=0, amplitudes_in_mA=[1, -1, 0], durations_in_ms=[0.1, 0.1, 1]
    )
    stg.start()
    stg.sleep(5000)
    stg.stop()
