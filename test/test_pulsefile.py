from stg.pulsefile import repeat_pulsefile, PulseFile, dump
import pytest


# @pytest.mark.parametrize("mode", ["biphasic", "monophasic"])
# @pytest.mark.parametrize("mA", [1, -1, 99999])


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
    with NamedTemporaryFile(suffix=".dat") as fname:
        pf.dump(fname.name)
        content = fname.readlines()
    exp = [
        b"Multi Channel Systems MC_Stimulus II\n",
        b"ASCII import Version 1.10\n",
        b"\n",
        b"channels: 2\n",
        b"\n",
        b"output mode: current\n",
        b"\n",
        b"format: 4\n",
        b"\n",
        b"channel: 1\n",
        b"\n",
        b"value\ttime\n",
        b"1\t100.0\n",
        b"-1\t100.0\n",
        b"0\t49800.0\n",
    ]
    for o, e in zip(content, exp):
        assert o == e

    with NamedTemporaryFile(suffix=".dat") as fname:
        dump([pf, pf], fname.name)
        content = fname.readlines()
    exp = [
        b"Multi Channel Systems MC_Stimulus II\n",
        b"ASCII import Version 1.10\n",
        b"\n",
        b"channels: 2\n",
        b"\n",
        b"output mode: current\n",
        b"\n",
        b"format: 4\n",
        b"\n",
        b"channel: 1\n",
        b"\n",
        b"value\ttime\n",
        b"1\t100.0\n",
        b"-1\t100.0\n",
        b"0\t49800.0\n",
        b"\n",
        b"channel: 2\n",
        b"\n",
        b"value\ttime\n",
        b"1\t100.0\n",
        b"-1\t100.0\n",
        b"0\t49800.0\n",
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
