from stg.api import PulseFile, STG4000
import pytest


@pytest.fixture(scope="module")
def stg():
    stg = STG4000()
    print(stg, stg.version)
    yield stg


def test_download(stg):
    p = PulseFile()
    stg.download(0, *p())
    for i in range(0, 100, 1):
        stg.start_stimulation([0])
        stg.sleep(0.01)

