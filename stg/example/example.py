# -*- coding: utf-8 -*-
"""
"""

from stg import PulseFile, STG4000

# %%
stg = STG4000()
print(stg, stg.version)
p = PulseFile()

stg.download(0, *p())
stg.start_stimulation([0])

stg.sleep(0.5)
p = PulseFile(intensity_in_mA=1, burstcount=600)
stg.download(0, *p())
stg.start_stimulation([0])
stg.stop_stimulation()


for i in range(0, 100, 1):
    p = PulseFile(intensity_in_mA=1000, pulsewidth_in_ms=1 * i)
    stg.download(0, *p())
    stg.start_stimulation([0])
    stg.sleep(0.5)

while True:
    p = PulseFile(intensity_in_mA=1, pulsewidth_in_ms=2)
    stg.download(0, *p())
    stg.start_stimulation([0, 1])
    stg.sleep(0.25)
