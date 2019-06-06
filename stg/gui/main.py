from PyQt5 import QtWidgets, uic
import sys
from functools import partial
from stg import STG4000, PulseFile
from stg.stm import dump
#%%
class Intensity():
    
    def __init__(self, labels, bumin, buplus, repetitive_button, download_foo, fuse):
        self.labels = labels
        self.repetitive_button = repetitive_button
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
        intensity = 0.
        for i, lbl in enumerate(reversed(self.labels)):            
            v  = float(lbl.text())        
            #print(i, 10**i, v, lbl.text())
            intensity += (v * (10**i))
        intensity = intensity*10 #in uA
        print('Set to ', intensity/1000, 'mA')
        burstcount= 60 if self.repetitive_button.isChecked() else 1
        isi = 49 if self.repetitive_button.isChecked() else 1
        p = PulseFile(intensity=intensity, 
                      mode='biphasic',
                      pulsewidth=.5,
                      burstcount=burstcount,                  
                      isi=isi)   
        return p
        
    def compile_and_download(self):
        p = self.compile()
        amplitude, duration = p()
        self.download(amplitude=amplitude, duration=duration)
        self.fuse.setEnabled(True)

class MainWindow(QtWidgets.QMainWindow):

    def trigger(self, channel):
        if channel == 0:
            print('Compiling for channel 1')
            if not self.ui.Arb_repetitive.isChecked():
                self.Aintensity.compile_and_download() 
            else:
                p = self.Aintensity.compile()
                p.burstcount= 60 
                self.device.download(0, *p())
        
        elif channel == 1:
            print('Compiling for channel 2')            
            if not self.ui.Brb_repetitive.isChecked():
                self.Bintensity.compile_and_download() 
            else:
                p = self.Bintensity.compile()
                p.burstcount= 60 
                self.device.download(1, *p())
                        
        self.device.start_stimulation([channel])
        self.ui.Fuse.setEnabled(True)
        
    def fuse(self):
         p = self.Aintensity.compile()
         p.burstcount= 1
         self.device.download(0, *p())
         p = self.Bintensity.compile()
         p.burstcount= 1
         self.device.download(1, *p())
         self.ui.Fuse.setEnabled(False)
        
    def __init__(self, parent=None):
        super().__init__(parent)
        self.device = STG4000()
        import os, pathlib
        os.chdir(pathlib.Path(__file__).parent)
        self.ui = uic.loadUi("mainwindow.ui", self)
        fuse = self.ui.Fuse
        self.ui.Device.setText(str(self.device))
        Aval = [self.ui.A1, self.ui.A2, self.ui.A3, self.ui.A4]        
        Amin = [self.ui.A1minus,self.ui.A2minus,self.ui.A3minus,self.ui.A4minus]
        Apls = [self.ui.A1plus,self.ui.A2plus,self.ui.A3plus,self.ui.A4plus]
        foo = partial(self.device.download, channel_index=0)
        self.Aintensity = Intensity(Aval, Amin, Apls, self.Arb_repetitive, foo, fuse)
        foo = partial(self.trigger, channel=0) 
        self.ui.Atrigger.clicked.connect(foo)
        
        Bval = [self.ui.B1,self.ui.B2, self.ui.B3, self.ui.B4]        
        Bmin = [self.ui.B1minus,self.ui.B2minus,self.ui.B3minus,self.ui.B4minus]
        Bpls = [self.ui.B1plus,self.ui.B2plus,self.ui.B3plus,self.ui.B4plus]
        foo = partial(self.device.download, channel_index=1)
        self.Bintensity = Intensity(Bval, Bmin, Bpls, self.Brb_repetitive, foo, fuse)
        foo = partial(self.trigger, channel=1) 
        self.ui.Btrigger.clicked.connect(foo)
          
        self.ui.StopAll.clicked.connect(lambda:self.device.stop_stimulation(all))
        self.ui.Fuse.clicked.connect(self.fuse)
        
# %%     
def main():    
    app = QtWidgets.QApplication(sys.argv)
    window = MainWindow()
#    self = window
    window.show()
    app.exec_()
    app.aboutToQuit.connect(lambda:print('Goodbye'))    

if __name__ == '__main__':
    main()