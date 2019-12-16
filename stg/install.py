"""Downloads and installs dll version 3.2.45
"""
import urllib.request
from zipfile import ZipFile
from pathlib import Path
import shutil

# %%
def download_dll():
    LIBPATH = Path(__file__).parent
    url = "http://download.multichannelsystems.com/download_data/software/McsNetUsb/McsUsbNet_3.2.45.zip"
    fname = LIBPATH / "bin" / "McsUsbNet_3.2.45.zip"
    print("Downloading to", str(fname), end="")
    fname, l = urllib.request.urlretrieve(url, filename=fname)
    print(". Finished")
    #
    print("Uzipping.", end="")
    with ZipFile(fname, "r") as f:
        d = f.extract("McsUsbNetPackage/x64/McsUsbNet.dll")

    source = Path(d)
    target = LIBPATH / "bin" / source.name
    shutil.move(source, target)
    print(" Unzipped file to", target)

    print("Cleaning up")
    shutil.rmtree(LIBPATH / "McsUsbNetPackage")
    Path(fname).unlink()


if __name__ == "__main__":
    download_dll()
