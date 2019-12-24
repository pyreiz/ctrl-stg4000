from itertools import chain, repeat, accumulate
from pathlib import Path
from typing import Tuple, List, Union

FileName = Union[Path, str]


class PulseFile:
    """Programmatically generate repetitive a biphasic or monophasic pulses

    args
    ----
    intensity_in_mA: float = 1
        the amplitude of the first rectangular pulse
    mode: str {"biphasic", "monophasic"} 
        whether the pulse will be monophasic of biphasic, i.e. followed by a rectangular pulse with inverted amplitude
    pulsewidth_in_ms: float = 0.1
        the width of each rectangular pulse
    burstcount: int = 1
        how often these pulses will be repeated
    isi_in_ms: float = 49.8
        how much time will pass between pulses


    After initialization, run  :meth:`~.compile` to generate amplitudes and durations. These can be downloadwed with STG4000s :meth:`~.stg._wrapper.downloadnet.STG4000.download`
    
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
        elif mode == "monophasic":
            intensity = [intensity_in_mA]
            pulsewidth = [pulsewidth_in_ms]
        else:
            raise NotImplementedError(f"Unknown mode {mode}")

        if pulsewidth_in_ms < 0:
            raise ValueError("Minimum PulseWidth must be 0ms")

        if burstcount < 1:
            raise ValueError("Minimum BurstCount must be 1")

        if isi_in_ms < 0:
            raise ValueError("Minimum ISI must be 0ms")

        self.intensity: List[float] = intensity
        self.pulsewidth: List[float] = pulsewidth
        self.mode: str = mode
        self.burstcount: int = burstcount
        self.isi: float = isi_in_ms

    def compile(self):
        """compile the pulsefile to compressed amps and durs

        returns
        ------
        amplitudes_in_mA: List[float]
            a list of amplitudes
        durations_in_ms: List[float]
            a list of durations

        """
        amps = [a for a in chain(self.intensity, [0])]
        durs = [d for d in chain(self.pulsewidth, [self.isi])]
        amps = chain(*repeat(amps, self.burstcount))  # repeat
        durs = chain(*repeat(durs, self.burstcount))  # repeat
        return list(amps), list(durs)

    @property
    def duration_in_ms(self):
        "the duration of the complete stimulation including all bursts"
        return self.burstcount * (sum(self.pulsewidth) + self.isi)

    def __call__(self):
        return self.compile()

    def dump(self, fname):
        dump([self], fname)


def init_datfile(filename: FileName):
    fname = Path(str(filename)).expanduser().absolute()
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


def encode(pulsefile, channel: int = 0) -> List[str]:
    """encode a pulsefile into ascii format

    args
    ----
    pulsefile:PulseFile
        a pulsefile
    channel:int
        the channel, indexing starts at 0

    returns
    -------

    content:str
        the content of the file
    """
    stim_info = [
        f"channel: {channel+1}\n",
        "\n",
        "value\ttime\n",
    ]  # : the header for every channel

    stim_commands = []
    for _ in range(0, pulsefile.burstcount):
        for amp, pw in zip(pulsefile.intensity, pulsefile.pulsewidth):
            newline = f"{amp}\t{pw*1000}\n"  # scale to µA/µs
            stim_commands.append(newline)

        newline = f"0\t{pulsefile.isi*1000}\n"  # scale to µs
        stim_commands.append(newline)

    stim_info.extend(stim_commands)
    return stim_info


def dump(pulsefiles: List[PulseFile], filename: FileName = "~/Desktop/test.dat"):
    """save Pulsefiles into a dat file readable by `MC Stimulus II <https://www.multichannelsystems.com/software/mc-stimulus-ii>`_

    args
    ----
    pulsefiles: List[PulseFile]
        a list of pulsefiles. The order defines the channel for which the respective pulsefile will be stored
    filename: Union[str, Path] = '~/Desktop/test.dat'
        the filename of the file
    """
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


def decompress(
    amplitudes_in_mA: List[float,] = [0],
    durations_in_ms: List[float,] = [0],
    rate_in_hz: int = 50_000,
) -> List[float]:
    """decompress amplitudes and durations into a continuously sampled signal
    
    args
    ------
    amplitudes_in_mA: List[float,] = [0]
        a list of amplitudes
    durations_in_ms: List[float,] = [0]
        a list of the respective durationas
    rate_in_hz: int = 50_000
        the sampling rate of the decompressed signal
    
    returns
    -------
    signal: List[float]
        a list of amplitudes comprising the signal continuously sampled at the given rate

    """
    if rate_in_hz not in [50_000, 10_000]:
        raise ValueError("Rate must be either 10 or 50kHz")
    rate_in_khz = rate_in_hz / 1000
    if len(amplitudes_in_mA) != len(durations_in_ms):
        raise ValueError("Every amplitude needs a duration and vice versa")

    signal = []
    for a, d in zip(amplitudes_in_mA, durations_in_ms):
        signal.extend([a] * int(d * rate_in_khz))
    return signal


# --------


def entrain(
    pulsefile: PulseFile, ibi_in_ms: float, count: int
) -> Tuple[List[float], List[float]]:
    """compile and repeat a pulsefile separated by ibi_in_ms

    args
    ----

    pulsefile: PulseFile
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
    inamps, indurs = pulsefile.compile()
    for cnt in range(count):
        if cnt == 0:
            amps, durs = inamps[:], indurs[:]
        else:
            amps += [0]
            durs += [ibi_in_ms]
            amps += inamps
            durs += indurs
    return amps, durs
