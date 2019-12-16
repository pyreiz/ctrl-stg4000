from pathlib import Path
from stg.install import DLLPATH, download_dll
import pytest
import sys


@pytest.mark.download
@pytest.mark.parametrize("platform", ["32bit", "64bit"])
def test_download_dll(platform):
    if DLLPATH.exists():
        DLLPATH.unlink()
    assert DLLPATH.exists() == False
    download_dll(platform)
    assert DLLPATH.exists()

