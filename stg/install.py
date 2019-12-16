"""Downloads and installs dll version 3.2.45
"""
import urllib.request
from zipfile import ZipFile
from pathlib import Path
import shutil
import platform

# %%
LIBPATH = Path(__file__).parent
DLLPATH = LIBPATH / "bin" / "McsUsbNet.dll"


def download_dll() -> None:
    "download the DLL in version 3.2.45 from multichannelsystems"
    url = "http://download.multichannelsystems.com/download_data/software/McsNetUsb/McsUsbNet_3.2.45.zip"
    fname = LIBPATH / "bin" / "McsUsbNet_3.2.45.zip"
    print("Downloading to", str(fname))
    fname, l = urllib.request.urlretrieve(url, filename=fname)
    print(". Finished")
    #
    print(f"Unzipping the {platform.architecture()[0]} dll...", end="")
    if platform.architecture()[0] == "64bit":
        member = "McsUsbNetPackage/x64/McsUsbNet.dll"
    else:
        member = "McsUsbNet.dll"

    with ZipFile(fname, "r") as f:
        d = f.extract(member)

    source = Path(d)
    target = LIBPATH / "bin" / source.name
    shutil.move(source, target)
    print(" Unzipped file to", target)

    print("Cleaning up")
    shutil.rmtree("McsUsbNetPackage")
    Path(fname).unlink()
    if not DLLPATH.exists():
        raise FileNotFoundError("DLL was not properly installed")


if __name__ == "__main__":
    if not DLLPATH.exists():
        download_dll()
