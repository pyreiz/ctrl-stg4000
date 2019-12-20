from stg.api import PulseFile, STG4000

# we initialize the STG and print information about it
stg = STG4000()
print(stg, stg.version)

# create a pulsefile with default parameters
p = PulseFile()
# compile the pulsefile and expand the tuple to positional arguments
# and download it into channel 1
# As you can see, indexing starts at zero
stg.download(0, *p())
# start stimulation at channel 1
stg.start_stimulation([0])

# sleep for 500ms
stg.sleep(500)
# create a new pulsefile consisting of 600 repetitve pulses
p = PulseFile(intensity_in_mA=1, burstcount=600)
stg.download(0, *p())
# start and immediatly stop it again
# this shows that an ongoing stimulation can be aborted
stg.start_stimulation([0])
stg.stop_stimulation()

# create a biphasic pulse with 1mA amplitude and a pulse-width of 2ms
# and trigger it every 250 ms
# timing is here determined by python and therefore necessarily not as exact
p = PulseFile(intensity_in_mA=1, pulsewidth_in_ms=2)
stg.download(0, *p())
while True:
    stg.start_stimulation([0, 1])
    stg.sleep(duration_in_ms=250)
