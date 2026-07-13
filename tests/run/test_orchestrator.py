from pathlib import Path
import fluka.run.orchestrator as orch
import fluka.run.orchestrator as O

SIM_YAML = """
general:
  input: example.inp
  backend: ts
  output: results/
  primaries: 1000
submit:
  njobs: 2
grid:
  parameters: { beame: [0.1] }
  runs_per_combo: 2
analysis:
  units: [21]
"""

def test_analyze_phase_runs_collect_then_analysis(tmp_path, monkeypatch):
    p = tmp_path / "sim.yaml"; p.write_text(SIM_YAML)
    calls = []
    monkeypatch.setattr(orch, "_run_collect", lambda sim: calls.append("collect"))
    monkeypatch.setattr(orch, "_run_analysis", lambda sim: calls.append("analysis"))
    orch.analyze_phase(p)
    assert calls == ["collect", "analysis"]


def _sim(tmp_path, *, custom_exe=True, grid=True):
    lines = ["general:", "  input: x.inp", "  backend: ts", "  output: out/",
             "  recompile: true", "submit:", "  njobs: 2"]
    if grid:
        lines += ["grid:", "  parameters: { beame: [0.1] }", "  runs_per_combo: 1"]
    if custom_exe:
        lines += ["custom_exe:", "  routines: [mgdraw.f]"]
    p = tmp_path / "sim.yaml"; p.write_text("\n".join(lines) + "\n"); return p

def test_launch_compiles_then_grid(tmp_path, monkeypatch):
    seen = {}
    monkeypatch.setattr(O, "compile_exe", lambda section, force: Path("/E"))
    monkeypatch.setattr(O, "_do_grid", lambda cfg, exe: seen.update(grid=exe))
    monkeypatch.setattr(O, "_do_submit", lambda cfg, exe: seen.update(submit=exe))
    O.launch(_sim(tmp_path, custom_exe=True, grid=True))
    assert seen.get("grid") == Path("/E") and "submit" not in seen

def test_launch_no_custom_exe_submit(tmp_path, monkeypatch):
    called = {"compile": False}
    monkeypatch.setattr(O, "compile_exe", lambda *a, **k: called.__setitem__("compile", True))
    monkeypatch.setattr(O, "_do_grid", lambda cfg, exe: None)
    monkeypatch.setattr(O, "_do_submit", lambda cfg, exe: called.__setitem__("submit_exe", exe))
    O.launch(_sim(tmp_path, custom_exe=False, grid=False))
    assert called["compile"] is False and called["submit_exe"] is None


def test_main_bare_argv_dispatches_to_launch(tmp_path, monkeypatch):
    seen = {}
    monkeypatch.setattr(O, "launch", lambda sim: seen.update(launch=sim))
    monkeypatch.setattr(O, "analyze_phase", lambda sim: seen.update(analyze=sim))
    monkeypatch.setattr("sys.argv", ["fluka-run", "cfg.yaml"])
    O.main()
    assert seen == {"launch": Path("cfg.yaml")}


def test_main_analyze_argv_dispatches_to_analyze_phase(tmp_path, monkeypatch):
    seen = {}
    monkeypatch.setattr(O, "launch", lambda sim: seen.update(launch=sim))
    monkeypatch.setattr(O, "analyze_phase", lambda sim: seen.update(analyze=sim))
    monkeypatch.setattr("sys.argv", ["fluka-run", "analyze", "cfg.yaml"])
    O.main()
    assert seen == {"analyze": Path("cfg.yaml")}
