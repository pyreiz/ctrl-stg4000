from stg._wrapper.streamingnet import STG4000
import pytest


@pytest.fixture(scope="module")
def stg():
    stg = STG4000()
    print(stg, stg.version)
    yield stg


@pytest.mark.stream
def test_streaming(stg):
    stg.stream()
