import pytest
from pathlib import Path
from fluka.cli._common import resolve, load_sim
from fluka.cli import submit


def test_common_reexports_resolve_merges_general_into_tool(tmp_path):
    p = tmp_path / "sim.yaml"
    p.write_text("general:\n  backend: ts\nanalysis:\n  units: [21]\n")
    cfg = resolve(p, "analysis")
    assert cfg["backend"] == "ts"    # from general
    assert cfg["units"] == [21]      # from tool section


def test_common_reexports_resolve_tool_overrides_general(tmp_path):
    p = tmp_path / "sim.yaml"
    p.write_text("general:\n  backend: ts\nsubmit:\n  backend: slurm\n")
    cfg = resolve(p, "submit")
    assert cfg["backend"] == "slurm"


def test_common_reexports_load_sim_returns_raw_sections(tmp_path):
    p = tmp_path / "sim.yaml"
    p.write_text("general:\n  backend: ts\nanalysis:\n  units: [21]\n")
    data = load_sim(p)
    assert data["analysis"]["units"] == [21]


def test_common_reexports_load_sim_requires_general(tmp_path):
    p = tmp_path / "sim.yaml"
    p.write_text("analysis: {units: [21]}\n")
    with pytest.raises(Exception):
        load_sim(p)


def test_submit_grid_does_not_submit_base_input_after_grid(monkeypatch):
    """Grid runner already submits each generated input; base submit would duplicate work."""
    calls = []
    monkeypatch.setattr("sys.argv", ["fluka-submit", "--grid", "sim.yaml"])
    monkeypatch.setattr("fluka.cli.grid.run_sim", lambda path: calls.append(("grid", path)))
    monkeypatch.setattr(submit, "run_sim", lambda path: calls.append(("submit", path)))
    submit.main()
    assert calls == [("grid", Path("sim.yaml"))]


def test_collect_sim_raises_on_nonzero_result(monkeypatch):
    monkeypatch.setattr(submit, "resolve", lambda path, tool: {"output": "/runs"})
    monkeypatch.setattr("fluka.queue.collect_results.main", lambda path: 1)

    with pytest.raises(submit.CollectionError, match="collection failed"):
        submit.collect_sim(Path("sim.yaml"))
