from stg.pulsefile import repeat_pulsefile, PulseFile, dump, decompress
import pytest
from pathlib import Path


# @pytest.mark.parametrize("mode", ["biphasic", "monophasic"])
# @pytest.mark.parametrize("mA", [1, -1, 99999])


def test_decompress():
    "test decompression of a 100µs biphasic pulse at 20Hz ISI"
    amplitudes_in_mA = [1, -1, 0]
    durations_in_ms = [0.1, 0.1, 49.8]
    rate_in_hz = 50_000
    signal = decompress(
        amplitudes_in_mA=amplitudes_in_mA,
        durations_in_ms=durations_in_ms,
        rate_in_hz=rate_in_hz,
    )
    assert len(signal) == 2500
    assert signal[0:5] == [1] * 5
    assert signal[5:10] == [-1] * 5
    assert signal[10:] == [0] * 2490

    with pytest.raises(ValueError):
        signal = decompress(rate_in_hz=1)

    with pytest.raises(ValueError):
        signal = decompress(amplitudes_in_mA=[1, 1], durations_in_ms=[0.1])


def test_pw_raises():
    with pytest.raises(ValueError):
        pf = PulseFile(pulsewidth_in_ms=-1)


def test_mode_compile_raises():
    with pytest.raises(NotImplementedError):
        pf = PulseFile(mode="notimplemented")


def test_bc_compile_raises():
    with pytest.raises(ValueError):
        pf = PulseFile(burstcount=-1)


def test_isi_compile_raises():
    with pytest.raises(ValueError):
        pf = PulseFile(isi_in_ms=-1)


@pytest.mark.parametrize("pw", [1, 0])
def test_pw_compile(pw):
    pf = PulseFile(
        intensity_in_mA=1,
        pulsewidth_in_ms=pw,
        mode="monophasic",
        burstcount=1,
        isi_in_ms=0,
    )
    amps, durs = pf.compile()
    assert durs[0] == pw


@pytest.mark.parametrize("mode", ["monophasic", "biphasic"])
def test_mode_compile(mode):
    pf = PulseFile(
        intensity_in_mA=1, pulsewidth_in_ms=1, mode=mode, burstcount=1, isi_in_ms=0,
    )
    amps, durs = pf.compile()
    assert amps[0] == 1
    if "mono" in mode:
        exp = 1
        assert len(amps) == 2
    elif "bi" in mode:
        exp = 2
        assert amps[1] == -1
    out = max(amps) - min(amps)
    assert out == exp


def test_duration_in_ms():
    pf = PulseFile(pulsewidth_in_ms=1, mode="biphasic", burstcount=1, isi_in_ms=48,)
    assert pf.duration_in_ms == 50


def test_call():
    pf = PulseFile()
    assert pf.compile() == pf()


def test_dump():
    from tempfile import NamedTemporaryFile

    with NamedTemporaryFile(suffix=".invalid") as fname:
        with pytest.raises(ValueError):
            dump([], fname.name)

    pf = PulseFile()
    fname = "test1.dat"
    # with NamedTemporaryFile(suffix=".dat") as fname:
    pf.dump(fname)
    with open(fname) as f:
        content = f.readlines()
    Path(fname).unlink()
    exp = [
        "Multi Channel Systems MC_Stimulus II\n",
        "ASCII import Version 1.10\n",
        "\n",
        "channels: 2\n",
        "\n",
        "output mode: current\n",
        "\n",
        "format: 4\n",
        "\n",
        "channel: 1\n",
        "\n",
        "value\ttime\n",
        "1\t100.0\n",
        "-1\t100.0\n",
        "0\t49800.0\n",
    ]
    for o, e in zip(content, exp):
        assert o == e

    fname = "test2.dat"
    dump([pf, pf], fname)
    with open(fname) as f:
        content = f.readlines()
    Path(fname).unlink()
    exp = [
        "Multi Channel Systems MC_Stimulus II\n",
        "ASCII import Version 1.10\n",
        "\n",
        "channels: 2\n",
        "\n",
        "output mode: current\n",
        "\n",
        "format: 4\n",
        "\n",
        "channel: 1\n",
        "\n",
        "value\ttime\n",
        "1\t100.0\n",
        "-1\t100.0\n",
        "0\t49800.0\n",
        "\n",
        "channel: 2\n",
        "\n",
        "value\ttime\n",
        "1\t100.0\n",
        "-1\t100.0\n",
        "0\t49800.0\n",
    ]
    for o, e in zip(content, exp):
        assert o == e


def test_repeat():
    pf = PulseFile()
    a, d = pf()
    amps, durs = repeat_pulsefile(pf, ibi_in_ms=1, count=2)
    assert amps[3] == 0
    assert durs[3] == 1
    assert durs[0:3] == durs[4:]
    assert amps[0:3] == amps[4:]
    assert durs[0:3] == d
    assert amps[0:3] == a
