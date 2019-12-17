from PyQt5 import QtWidgets, uic
from PyQt5.QtWidgets import QFileDialog
import sys
import pathlib
from functools import partial
from stg.api import STG4000, PulseFile
from stg.pulsefile import dump

#%%
class Intensity:
    def __init__(self, labels, bumin, buplus, repetitive_button, download_foo, fuse):
        self.labels = labels
        self.bc = 1
        self.isi = 1
        self.repetitive_button = repetitive_button
        self.repetitive_button.toggled.connect(self.burstcount_was_changed)
        self.download = download_foo
        self.fuse = fuse
        for l, b in zip(labels, bumin):
            b.clicked.connect(partial(self.decrease, l))

        for l, b in zip(labels, buplus):
            b.clicked.connect(partial(self.increase, l))

    def increase(self, label):
        cur = int(label.text())
        cur += 1
        if cur > 9:
            cur = 0
        label.setText(str(cur))
        self.compile_and_download()

    def decrease(self, label):
        cur = int(label.text())
        cur -= 1
        if cur < 0:
            cur = 9
        label.setText(str(cur))
        self.compile_and_download()

    def compile(self):
        intensity = 0.0
        for i, lbl in enumerate(reversed(self.labels)):
            v = float(lbl.text())
            # print(i, 10**i, v, lbl.text())
            intensity += v * (10 ** i)
        intensity = intensity * 10  # in uA
        print(
            "Set to ",
            intensity / 1000,
            "mA",
            self.bc,
            " pulses at ",
            1000 / (1 + self.isi),
            "Hz",
        )

        p = PulseFile(
            intensity_in_mA=intensity,
            mode="biphasic",
            pulsewidth_in_ms=0.5,
            burstcount=self.bc,
            isi_in_ms=self.isi,
        )
        return p

    def burstcount_was_changed(self):

        self.bc = 60 if self.bc == 1 else 1
        self.isi = 49 if self.isi == 1 else 1
        self.compile_and_download()

    def compile_and_download(self):
        p = self.compile()
        amplitude, duration = p()
        self.download(amplitudes_in_mA=amplitude, durations_in_ms=duration)
        self.fuse.setEnabled(True)


class MainWindow(QtWidgets.QMainWindow):
    def trigger(self, channel):
        if channel == 0:
            print("Compiling for channel 1")
            self.Aintensity.compile_and_download()

        elif channel == 1:
            print("Compiling for channel 2")
            self.Bintensity.compile_and_download()

        self.device.start_stimulation([channel])
        self.ui.Fuse.setEnabled(True)

    def fuse(self):
        print("Fusing")
        self.ui.Arb_sp.setChecked(True)
        self.ui.Brb_sp.setChecked(True)
        p0 = self.Aintensity.compile()
        self.device.download(0, *p0())
        p1 = self.Bintensity.compile()
        self.device.download(1, *p1())
        self.ui.Fuse.setEnabled(False)
        return (p0, p1)

    def export(self):
        path = pathlib.Path("~/Desktop").expanduser().absolute()
        options = QFileDialog.Options()
        options |= QFileDialog.DontUseNativeDialog
        filename, _ = QFileDialog.getSaveFileName(
            self,
            "QFileDialog.getSaveFileName()",
            str(path),
            "Dat Files (*.dat);;All Files (*)",
            options=options,
        )
        if filename:
            (p0, p1) = self.fuse()
            dump(filename=filename, pulsefiles=(p0, p1))
            print(f"Saving to {filename}")

    def __init__(self, parent=None):
        super().__init__(parent)
        import os, pathlib

        os.chdir(pathlib.Path(__file__).parent)
        self.device = STG4000()
        self.ui = uic.loadUi("mainwindow.ui", self)
        fuse = self.ui.Fuse
        self.ui.Device.setText(str(self.device))
        Aval = [self.ui.A1, self.ui.A2, self.ui.A3, self.ui.A4]
        Amin = [self.ui.A1minus, self.ui.A2minus, self.ui.A3minus, self.ui.A4minus]
        Apls = [self.ui.A1plus, self.ui.A2plus, self.ui.A3plus, self.ui.A4plus]
        foo = partial(self.device.download, channel_index=0)
        self.Aintensity = Intensity(Aval, Amin, Apls, self.Arb_repetitive, foo, fuse)
        foo = partial(self.trigger, channel=0)
        self.ui.Atrigger.clicked.connect(foo)

        Bval = [self.ui.B1, self.ui.B2, self.ui.B3, self.ui.B4]
        Bmin = [self.ui.B1minus, self.ui.B2minus, self.ui.B3minus, self.ui.B4minus]
        Bpls = [self.ui.B1plus, self.ui.B2plus, self.ui.B3plus, self.ui.B4plus]
        foo = partial(self.device.download, channel_index=1)
        self.Bintensity = Intensity(Bval, Bmin, Bpls, self.Brb_repetitive, foo, fuse)
        foo = partial(self.trigger, channel=1)
        self.ui.Btrigger.clicked.connect(foo)

        self.ui.StopAll.clicked.connect(lambda: self.device.stop_stimulation(all))
        self.ui.Fuse.clicked.connect(self.fuse)
        self.ui.Export.clicked.connect(self.export)

    def closeEvent(self, event):
        self.fuse()


# %%
def main():
    app = QtWidgets.QApplication(sys.argv)
    window = MainWindow()
    #    self = window
    window.show()
    app.exec_()

    def on_close():
        print("Shutting down")

    app.aboutToQuit.connect(on_close)


if __name__ == "__main__":
    main()
