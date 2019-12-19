from stg._wrapper.streamingnet import STG4000Streamer
import pytest


@pytest.fixture
def stg():
    stg = STG4000Streamer()
    assert stg.output_rate_in_khz == 50
    assert stg._signals.keys() == []
    assert stg.buffer_size == 100
    yield stg


def test_properties(stg):
    stg.buffer_size = 99
    assert stg.buffer_size == 99
