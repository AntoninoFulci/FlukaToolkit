import fluka.run.orchestrator as orch

def test_submit_phase_runs_grid_then_submit(tmp_path, monkeypatch):
    p = tmp_path / "sim.yaml"; p.write_text("grid: {}\nsubmit: {}\n")
    calls = []
    monkeypatch.setattr(orch, "_run_grid", lambda sim: calls.append("grid"))
    monkeypatch.setattr(orch, "_run_submit", lambda sim: calls.append("submit"))
    orch.submit_phase(p, do_grid=True)
    assert calls == ["grid", "submit"]

def test_submit_phase_skips_grid_when_disabled(tmp_path, monkeypatch):
    p = tmp_path / "sim.yaml"; p.write_text("submit: {}\n")
    calls = []
    monkeypatch.setattr(orch, "_run_grid", lambda sim: calls.append("grid"))
    monkeypatch.setattr(orch, "_run_submit", lambda sim: calls.append("submit"))
    orch.submit_phase(p, do_grid=False)
    assert calls == ["submit"]

def test_analyze_phase_runs_collect_then_analysis(tmp_path, monkeypatch):
    p = tmp_path / "sim.yaml"; p.write_text("analysis: {}\n")
    calls = []
    monkeypatch.setattr(orch, "_run_collect", lambda sim: calls.append("collect"))
    monkeypatch.setattr(orch, "_run_analysis", lambda sim: calls.append("analysis"))
    orch.analyze_phase(p)
    assert calls == ["collect", "analysis"]
