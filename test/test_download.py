from stg.api import PulseFile, STG4000
import pytest
from stg._wrapper.dll import available, select
import time


@pytest.fixture(scope="module")
def stg():
    there = available()
    snum = int(there[0].SerialNumber)
    pick = select(snum)
    assert pick == there[0]
    stg = STG4000()
    print(stg, stg.version)
    yield stg


@pytest.mark.download
def test_download_current(stg):
    stg.download(
        channel_index=0,
        amplitudes_in_mA=[1, -1],
        durations_in_ms=[0.1, 0.1],
        mode="current",
    )
    t0 = time.time()
    while time.time() - t0 < 10:
        stg.start_stimulation([0])
        stg.sleep(10)


def test_mismatched_download(stg):
    with pytest.raises(ValueError):
        stg.download(0, amplitudes_in_mA=[1, 0], durations_in_ms=[0])


def test_current(stg):
    stg.download(
        channel_index=0,
        amplitudes_in_mA=[1, -1, 0],
        durations_in_ms=[0.1, 0.1, 0.488],
        mode="current",
    )
    stg.start_stimulation([0])
    stg.stop_stimulation([0])


def test_voltage(stg):
    stg.download(
        channel_index=0,
        amplitudes_in_mA=[1, -1, 0],
        durations_in_ms=[0.1, 0.1, 0.488],
        mode="voltage",
    )
    stg.start_stimulation([0])
    stg.stop_stimulation([0])


def test_start_stop_all(stg):
    stg.start_stimulation()
    stg.stop_stimulation()

