from stg._wrapper.mock import CStg200xMockNet, _mock
from stg._wrapper.dll import BasicInterface


def test_basic_interface(capsys):
    with BasicInterface("test") as interface:
        pass


def test_mock(capsys):
    device = CStg200xMockNet()
    device.Connect(None)
    device.Disconnect()
    pipe = capsys.readouterr()
    assert "MOCK:CONNECT" in pipe.out
    assert "MOCK:DISCONNECT" in pipe.out

    _mock(2, key="item")
    pipe = capsys.readouterr()
    assert "Mocking a call with (2,) {'key': 'item'}" in pipe.out
