from stg._wrapper.mock import CStg200xMockNet, _mock, DeviceInfo
from stg._wrapper.dll import BasicInterface, MockingInterface
import pytest
from stg._wrapper.streamingnet import STG4000Streamer


def test_basic_interface(capsys):
    with pytest.raises(TypeError):
        with BasicInterface("test") as interface:
            pass


def test_mock(capsys):
    with MockingInterface("test") as device:
        device.connect()
        device.disconnect()
        pipe = capsys.readouterr()
        assert "MOCK:CONNECT" in pipe.out
        assert "MOCK:DISCONNECT" in pipe.out

        _mock(2, key="item")
        pipe = capsys.readouterr()
        assert "Mocking a call with (2,) {'key': 'item'}" in pipe.out


@pytest.fixture
def stg(monkeypatch):
    def monkey(*args, **kwargs):
        return MockingInterface(DeviceInfo)

    monkeypatch.setattr(STG4000Streamer, "interface", monkey)
    monkeypatch.setattr(STG4000Streamer, "streamer", monkey)
    stg = STG4000Streamer(-1)
    yield stg


def test_repr(stg):
    assert "Mock at" in repr(stg)


field_values = [
    ("name", "STG0007"),
    ("serial_number", 70007),
    ("version", "Hardware - M-Hard : Software - Version: M-Soft"),
    ("channel_count", 2),
    ("current_range_in_mA", 16.0),
    ("current_range_in_uA", 16000.0),
    ("current_resolution_in_mA", 0.002),
    ("current_resolution_in_uA", 2.0),
    ("DAC_resolution", 14),
    ("time_resolution_in_ms", 0.02),
    ("time_resolution_in_us", 20),
    ("voltage_resolution_in_uV", 1000),
    ("voltage_range_in_uV", 8000.0),
    ("trigin_count", 2),
    ("manufacturer", "ACME"),
]


@pytest.mark.parametrize("field, value", field_values)
def test_properties(stg, field, value):
    assert getattr(stg, field) == value


def test_set_mode(stg):
    stg.set_mode(mode="current")
    stg.set_mode(mode="voltage")
