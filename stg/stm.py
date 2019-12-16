# -*- coding: utf-8 -*-
"""
Created on Tue Jun  4 14:38:43 2019

@author: Robert Guggenberger
"""
from itertools import chain, repeat, accumulate
from pathlib import Path
from typing import Tuple, List, Union

FileName = Union[Path, str]
# %%


def init_datfile(filename: FileName = "~/Desktop/test.dat"):
    fname = Path(str(filename)).expanduser().absolute()
    if fname.suffix == "":
        fname = fname.with_suffix(".dat")
    if fname.suffix != ".dat":
        raise ValueError("Only .dat files can be saved")

    stim_info = [
        "Multi Channel Systems MC_Stimulus II\n",
        "ASCII import Version 1.10\n",
        "\n",
        "channels: 2\n",
        "\n",
        "output mode: current\n",
        "\n",
        "format: 4\n",
        "\n",
    ]  # : the header for every MCS II .dat file

    with fname.open("w") as f:
        for line in stim_info:
            f.write(line)


# ---------


def encode(pulsefile, channel: int = 0):
    """encode a pulsefile into ascii format

    args
    ----
    pulsefile:PulseFile
        a pulsefile
    channel:int
        the channel, indexing starts at 0
    """
    stim_info = [
        f"channel: {channel+1}\n",
        "\n",
        "value\ttime\n",
    ]  # : the header for every channel

    stim_commands = []
    for bc in range(0, pulsefile.burstcount):
        for amp, pw in zip(pulsefile.intensity, pulsefile.pulsewidth):
            newline = f"{amp}\t{pw*1000}\n"  # scale to µA/µs

            stim_commands.append(newline)

        newline = f"0\t{pulsefile.isi*1000}\n"  # scale to µs
        stim_commands.append(newline)

    stim_info.extend(stim_commands)
    return stim_info


def dump(pulsefiles: List[PulseFile], filename: FileName = "~/Desktop/test.dat"):
    fname = Path(str(filename)).expanduser().absolute()
    init_datfile(fname)
    with fname.open("r") as f:
        lines = f.readlines()
    for idx, pulsefile in enumerate(pulsefiles):
        if idx > 0:
            lines.append("\n")
        lines.extend(encode(pulsefile, channel=idx))
    with fname.open("w") as f:
        for line in lines:
            f.write(line)


# --------


class PulseFile:
    """STG4000 signal

    A thin wrapper for the parametric generation of stimulation signals
    """

    def __init__(
        self,
        intensity_in_mA: float = 1,
        mode: str = "biphasic",
        pulsewidth_in_ms: float = 0.1,
        burstcount: int = 1,
        isi_in_ms: float = 49.8,
    ):

        if mode == "biphasic":
            intensity = [intensity_in_mA, -intensity_in_mA]
            pulsewidth = [pulsewidth_in_ms, pulsewidth_in_ms]
        else:
            intensity = [intensity_in_mA]
            pulsewidth = [pulsewidth_in_ms]

        self.intensity: List[float] = intensity
        self.pulsewidth: List[float] = pulsewidth
        self.mode: str = mode
        self.burstcount: int = burstcount
        self.isi: float = isi_in_ms

    def compile(self):
        """compile the pulsefile to amps and durs
        returns
        ------
        amps: List[float]
            a list of amplitudes
        durs: List[float]
            a list of durations
        """
        amps = [a for a in chain(self.intensity, [0])]
        durs = [d for d in chain(self.pulsewidth, [self.isi])]
        amps = chain(*repeat(amps, self.burstcount))  # repeat
        durs = chain(*repeat(durs, self.burstcount))  # repeat
        return list(amps), list(durs)

    @property
    def duration_in_ms(self):
        "returns the total expected duration of stimulation"
        return self.burstcount * (sum(self.pulsewidth) + self.isi)

    def __call__(self):
        return self.compile()

    def dump(self, fname):
        dump(fname, self)


def repeat_bursts(
    pf: PulseFile, ibi_in_ms: float, count: int
) -> Tuple[List[float], List[float]]:
    """compile and repeat a pulsefile separated by ibi_in_ms

    args
    ----

    pf: PulseFile
        defines a burst
    ibi_in_ms: float
        how long to wait between bursts
    count: int
        how many bursts you want to apply


    returns
    ------
    amps: List[float]
        a list of amplitudes
    durs: List[float]
        a list of durations
    """
    inamps, indurs = pf.compile()
    for cnt in range(count):
        if cnt == 0:
            amps, durs = inamps[:], indurs[:]
        else:
            amps += [0]
            durs += [ibi_in_ms]
            amps += inamps
            durs += indurs
    return amps, durs
