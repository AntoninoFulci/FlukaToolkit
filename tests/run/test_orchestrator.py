import fluka.run.orchestrator as orch

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

def test_submit_phase_runs_grid_then_submit(tmp_path, monkeypatch):
    p = tmp_path / "sim.yaml"; p.write_text(SIM_YAML)
    calls = []
    monkeypatch.setattr(orch, "_run_grid", lambda sim: calls.append("grid"))
    monkeypatch.setattr(orch, "_run_submit", lambda sim: calls.append("submit"))
    orch.submit_phase(p, do_grid=True)
    assert calls == ["grid", "submit"]

def test_submit_phase_skips_grid_when_disabled(tmp_path, monkeypatch):
    p = tmp_path / "sim.yaml"; p.write_text(SIM_YAML)
    calls = []
    monkeypatch.setattr(orch, "_run_grid", lambda sim: calls.append("grid"))
    monkeypatch.setattr(orch, "_run_submit", lambda sim: calls.append("submit"))
    orch.submit_phase(p, do_grid=False)
    assert calls == ["submit"]

def test_analyze_phase_runs_collect_then_analysis(tmp_path, monkeypatch):
    p = tmp_path / "sim.yaml"; p.write_text(SIM_YAML)
    calls = []
    monkeypatch.setattr(orch, "_run_collect", lambda sim: calls.append("collect"))
    monkeypatch.setattr(orch, "_run_analysis", lambda sim: calls.append("analysis"))
    orch.analyze_phase(p)
    assert calls == ["collect", "analysis"]
