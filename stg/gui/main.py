from PyQt5 import QtWidgets, uic
import sys
from functools import partial
import stg4x
from stg4x.helper import get_default_buildfilename, get_buildfilename
#%%
class Intensity():
    
    def __init__(self, labels, bumin, buplus, triggerbutton, fusebutton):
        self.labels = labels
        self.triggerbutton = triggerbutton
        self.fusebutton = fusebutton
        for l, b in zip(labels, bumin):
            b.clicked.connect(partial(self.decrease, l))
            
        for l, b in zip(labels, buplus):
            b.clicked.connect(partial(self.increase, l))
            
    def increase(self, label):
        self.triggerbutton.setEnabled(False)
        self.fusebutton.setEnabled(True)
        self.fusebutton.setText('Fuse')
        cur = int(label.text())
        cur += 1
        if cur > 9:
            cur = 0            
        label.setText(str(cur))
        self.get()
        
    def decrease(self, label):
        self.triggerbutton.setEnabled(False)
        self.fusebutton.setEnabled(True)
        self.fusebutton.setText('Fuse')
        cur = int(label.text())
        cur -= 1
        if cur < 0:
            cur = 9            
        label.setText(str(cur))
        self.get()
        
    def get(self):
        val = 0.
        for i, lbl in enumerate(reversed(self.labels)):            
            v  = float(lbl.text())        
            #print(i, 10**i, v, lbl.text())
            val += (v * (10**i))
        val = (val/100)
        print(val)
        return val

def download():
    gui = stg4x.mcsGUI()
    gui.open()
    gui.download()
    gui.close()
    
def trigger(channel=0):
    gui = stg4x.mcsGUI()
    gui.open()
    gui.trigger_now(channel)
    gui.close()
        
class MainWindow(QtWidgets.QMainWindow):

    
    def compile_download(self, channel):
        Aval = self.Aintensity.get() 
        Bval = self.Bintensity.get()
        Abc = 60 if self.ui.Arb_repetitive.isChecked() else 1
        Bbc = 60 if self.ui.Brb_repetitive.isChecked() else 1        
        
        if channel == 1:
            stm = stg4x.PulseFile(intensity=(Aval*1000, 0*1000),
                                  mode=('biphasic','biphasic'),
                                  burstcount=(Abc, Bbc),
                                  pulsewidth=(500, 500),
                                  isi= (49000, 49000))    
        else:
            stm = stg4x.PulseFile(intensity=(0*1000, Bval*1000),
                                  mode=('biphasic','biphasic'),
                                  burstcount=(Abc, Bbc),
                                  pulsewidth=(500, 500),
                                  isi= (49000, 49000))        
                            
        bfile = get_buildfilename(f'intervention_{channel}')
        self.ini.set_filemode('single')
        stg4x.compile_stm(stm, build_fname=bfile)              
        self.ini.set_filemode('mf8')
        self.ini.set_trigger(channel-1, bfile)        
        download()
        if channel == 1:
            self.ui.Atrigger.setEnabled(True)
        if channel == 2:
            self.ui.Btrigger.setEnabled(True)
        self.ui.Fuse.setEnabled(True)
        
    def fuse(self):
        Aval = self.Aintensity.get()
        Bval = self.Bintensity.get()
        stm = stg4x.PulseFile(intensity=(Aval*1000, Bval*1000),
                              mode=('biphasic','biphasic'),
                              burstcount=(1, 1),
                              pulsewidth=(500, 500),
                              isi= (500, 500))
        
        bfile = get_default_buildfilename()
        self.ini.set_filemode('single')
        bfile = stg4x.compile_stm(stm, build_fname=bfile)                          
        self.ini.set_trigger(2, bfile)
        self.ui.Fuse.setText('Now set Triggermode manually!')
        self.ui.Fuse.setEnabled(False)
        
    def __init__(self, parent=None):
        super().__init__(parent)
        self.ini = stg4x.mcsINI()
        self.ini.set_filemode('mf8')
        self.ini.enable_download(1)
        self.ini.enable_download(2)
        self.ini.set_individual_channel_mode(True)
        
        self.ui = uic.loadUi("mainwindow.ui", self)
        Aval = [self.ui.A1, self.ui.A2, self.ui.A3, self.ui.A4]        
        Amin = [self.ui.A1minus,self.ui.A2minus,self.ui.A3minus,self.ui.A4minus]
        Apls = [self.ui.A1plus,self.ui.A2plus,self.ui.A3plus,self.ui.A4plus]
        self.Aintensity = Intensity(Aval, Amin, Apls, self.Atrigger, self.Fuse)

        Bval = [self.ui.B1,self.ui.B2, self.ui.B3, self.ui.B4]        
        Bmin = [self.ui.B1minus,self.ui.B2minus,self.ui.B3minus,self.ui.B4minus]
        Bpls = [self.ui.B1plus,self.ui.B2plus,self.ui.B3plus,self.ui.B4plus]
        self.Bintensity = Intensity(Bval, Bmin, Bpls, self.Btrigger, self.Fuse)
    
        foo = partial(self.compile_download, channel=1) #needs to be single pulse
        self.ui.Acompile.clicked.connect(foo)
        foo = partial(self.compile_download, channel=2) #needs to be single pulse
        self.ui.Bcompile.clicked.connect(foo)
    
        self.ui.Atrigger.clicked.connect(partial(trigger, 0))
        self.ui.Btrigger.clicked.connect(partial(trigger, 1))
        self.ui.Fuse.clicked.connect(self.fuse)
# %%     
app = QtWidgets.QApplication(sys.argv)
window = MainWindow()
self = window
#%%
window.show()
sys.exit(app.exec_())
    

