# tests/run/test_root_routines_present.py
from importlib.resources import files

def _routines_dir():
    return files("fluka").joinpath("root_output", "routines")

def test_default_routines_shipped():
    d = _routines_dir()
    for name in ("usrini.f", "usrout.f", "mgdraw.f"):
        assert (d / name).is_file(), f"missing default routine {name}"

def test_mgdraw_stub_is_fortran_subroutine():
    txt = (_routines_dir() / "mgdraw.f").read_text().upper()
    assert "SUBROUTINE MGDRAW" in txt and "END" in txt
