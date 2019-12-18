from stg._wrapper.mock import CStg200xMockNet, _mock
from stg._wrapper.dll import BasicInterface, MockingInterface
import pytest


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
