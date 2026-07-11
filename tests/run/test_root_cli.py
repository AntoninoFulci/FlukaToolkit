from pathlib import Path
from fluka.cli.root import resolve_routines, build_command

def _defaults(tmp_path):
    d = tmp_path / "routines"; d.mkdir()
    for n in ("usrini.f", "usrout.f", "mgdraw.f"):
        (d / n).write_text(f"* default {n}\n")
    return d

def test_resolve_routines_defaults_only(tmp_path):
    d = _defaults(tmp_path)
    got = {p.name for p in resolve_routines([], d)}
    assert got == {"usrini.f", "usrout.f", "mgdraw.f"}

def test_resolve_routines_override_mgdraw(tmp_path):
    d = _defaults(tmp_path)
    mine = tmp_path / "mgdraw.f"; mine.write_text("* mine\n")
    resolved = resolve_routines([str(mine)], d)
    names = {p.name for p in resolved}
    assert names == {"usrini.f", "usrout.f", "mgdraw.f"}
    mg = next(p for p in resolved if p.name == "mgdraw.f")
    assert mg.read_text() == "* mine\n"           # override wins

def test_resolve_routines_extra(tmp_path):
    d = _defaults(tmp_path)
    extra = tmp_path / "source.f"; extra.write_text("* extra\n")
    names = {p.name for p in resolve_routines([str(extra)], d)}
    assert names == {"usrini.f", "usrout.f", "mgdraw.f", "source.f"}

def test_build_command_ttree(tmp_path):
    cmd = build_command({"rntuple": False, "routines": []},
                        root_dir="/x/root_output", build_dir="/tmp/b")
    joined = " ".join(cmd)
    assert cmd[0] == "make" and "-C" in cmd and "/tmp/b" in joined
    assert "USE_RNTUPLE=0" in joined
    assert 'OBJS=' in joined and "usrini.o" in joined and "mgdraw.o" in joined

def test_build_command_rntuple_and_name_and_extra(tmp_path):
    cmd = build_command({"rntuple": True, "name": "myexe",
                         "routines": [str(tmp_path / "source.f")]},
                        root_dir="/x/root_output", build_dir="/tmp/b")
    joined = " ".join(cmd)
    assert "USE_RNTUPLE=1" in joined and "NAME=myexe" in joined
    assert "source.o" in joined
