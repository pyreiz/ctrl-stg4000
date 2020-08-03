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


def download_dll(platform: str) -> None:
    "download the DLL in version 3.2.45 from multichannelsystems"
    url = "http://download.multichannelsystems.com/download_data/software/McsNetUsb/McsUsbNet_3.2.45.zip"
    fname = LIBPATH / "bin" / "McsUsbNet_3.2.45.zip"
    print("Downloading to", str(fname))
    dlname, l = urllib.request.urlretrieve(url, filename=fname)
    print(". Finished")

    # unzip

    print(f"Unzipping the {platform} dll...", end="")
    if platform == "64bit":
        member = "McsUsbNetPackage/x64/McsUsbNet.dll"
    else:
        member = "McsUsbNetPackage/McsUsbNet.dll"
    with ZipFile(fname, "r") as f:
        dll = f.extract(member)

    # move to desired position
    source = Path(dll)
    target = LIBPATH / "bin" / source.name
    shutil.move(str(source), target)
    print(" Unzipped file to", target)

    print("Cleaning up")
    shutil.rmtree("McsUsbNetPackage")
    Path(fname).unlink()
    if not DLLPATH.exists():
        raise FileNotFoundError("DLL was not properly installed")


if __name__ == "__main__":
    if not DLLPATH.exists():
        download_dll(platform.architecture()[0])
