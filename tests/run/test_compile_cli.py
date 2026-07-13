from pathlib import Path
from fluka.cli.compile import resolve_routines, build_command

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
    d = _defaults(tmp_path)
    routines = resolve_routines([], d)
    cmd = build_command({"rntuple": False}, "/tmp/b", routines)
    joined = " ".join(cmd)
    assert cmd[0] == "make" and "-C" in cmd and "/tmp/b" in joined
    assert "USE_RNTUPLE=0" in joined
    assert 'OBJS=' in joined and "usrini.o" in joined and "mgdraw.o" in joined

def test_build_command_rntuple_and_name_and_extra(tmp_path):
    d = _defaults(tmp_path)
    routines = resolve_routines([str(tmp_path / "source.f")], d)
    cmd = build_command({"rntuple": True, "name": "myexe"}, "/tmp/b", routines)
    joined = " ".join(cmd)
    assert "USE_RNTUPLE=1" in joined and "NAME=myexe" in joined
    assert "source.o" in joined


import subprocess
from fluka.cli.compile import compile_exe

def test_resolve_routines_use_defaults_false_only_listed(tmp_path):
    d = _defaults(tmp_path)
    mine = tmp_path / "mine.f"; mine.write_text("* mine\n")
    got = [p.name for p in resolve_routines([str(mine)], d, use_defaults=False)]
    assert got == ["mine.f"]                            # no defaults injected

def test_resolve_routines_false_warns_without_usrini(tmp_path, capsys):
    d = _defaults(tmp_path)
    mine = tmp_path / "mine.f"; mine.write_text("* mine\n")
    resolve_routines([str(mine)], d, use_defaults=False)
    assert "usrini" in capsys.readouterr().err.lower()  # warning on stderr

def test_build_command_objs_from_resolved(tmp_path):
    d = _defaults(tmp_path)
    routines = resolve_routines([str(tmp_path / "extra.f")], d, use_defaults=True)
    cmd = build_command({"rntuple": True, "name": "myexe"}, "/tmp/b", routines)
    j = " ".join(cmd)
    assert "USE_RNTUPLE=1" in j and "NAME=myexe" in j
    assert "usrini.o" in j and "usrout.o" in j and "mgdraw.o" in j and "extra.o" in j

def test_compile_exe_persists_and_skips(tmp_path, monkeypatch):
    d = _defaults(tmp_path)
    exe = tmp_path / "out" / "fluka_custom_exe"
    calls = {"make": 0}
    def fake_run(cmd, **kw):
        calls["make"] += 1
        bi = cmd.index("-C"); build_dir = Path(cmd[bi + 1])
        name = next(a.split("=", 1)[1] for a in cmd if a.startswith("NAME="))
        outp = build_dir / "RootFlukaExecutables" / name
        outp.parent.mkdir(parents=True, exist_ok=True); outp.write_text("BIN")
        return subprocess.CompletedProcess(cmd, 0, "", "")
    monkeypatch.setattr(subprocess, "run", fake_run)
    monkeypatch.setattr("fluka.cli.compile._DEFAULTS_DIR", d)
    section = {"routines": [], "name": "rootfluka", "exe_path": str(exe)}
    got = compile_exe(section, force=True)
    assert Path(got) == exe and exe.read_text() == "BIN" and calls["make"] == 1
    compile_exe(section, force=False)      # exists, not forced -> skip
    assert calls["make"] == 1
    compile_exe(section, force=True)       # forced -> rebuild
    assert calls["make"] == 2
