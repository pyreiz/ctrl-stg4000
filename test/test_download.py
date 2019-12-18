from stg.api import PulseFile, STG4000
import pytest


@pytest.fixture(scope="module")
def stg():
    stg = STG4000()
    print(stg, stg.version)
    yield stg


def test_download_current(stg):
    stg.download(
        channel_index=0,
        amplitudes_in_mA=[1000, -1000],
        durations_in_ms=[0.1, 0.1],
        mode="current",
    )
    for i in range(0, 100, 1):
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


def test_voltage(stg):
    stg.download(
        channel_index=0,
        amplitudes_in_mA=[1, -1, 0],
        durations_in_ms=[0.1, 0.1, 0.488],
        mode="voltage",
    )
    stg.start_stimulation([0])

