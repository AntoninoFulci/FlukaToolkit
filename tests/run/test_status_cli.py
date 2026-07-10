import json
from pathlib import Path
import pytest
import fluka.cli.status as C
from fluka.run.manifest import Job, record_job, manifest_path_for
from fluka.run import status as S


def _write_manifest(out_dir, backend="ts"):
    record_job(manifest_path_for(out_dir),
               Job(combo="c1", run_idx=1, run_name="run_0001",
                   run_dir=str(out_dir / "c1" / "run_0001"), backend=backend,
                   job_id="1", input_file="s.inp", submitted_at="t", extra={}))

def _sim_yaml(tmp_path, out_dir):
    p = tmp_path / "sim.yaml"
    p.write_text(f"grid:\n  output:\n    directory: {out_dir}\n")
    return p

def test_output_dir_helper():
    assert C._output_dir({"output": {"directory": "/out"}}) == Path("/out")

def test_output_dir_missing_raises():
    with pytest.raises(Exception):
        C._output_dir({})

def test_build_status_reports_done(tmp_path):
    out = tmp_path / "results"; (out / "c1" / "run_0001").mkdir(parents=True)
    (out / "c1" / "run_0001" / ".fluka_status").write_text("FLUKA_STATUS rc=0")
    _write_manifest(out)
    sim = _sim_yaml(tmp_path, out)
    statuses = C.build_status(sim)
    assert len(statuses) == 1 and statuses[0].state == S.DONE

def test_render_table_contains_states(tmp_path):
    out = tmp_path / "results"; (out / "c1" / "run_0001").mkdir(parents=True)
    (out / "c1" / "run_0001" / ".fluka_status").write_text("FLUKA_STATUS rc=0")
    _write_manifest(out)
    sim = _sim_yaml(tmp_path, out)
    txt = C.render_table(C.build_status(sim))
    assert "DONE" in txt and "run_0001" in txt

def test_missing_manifest_errors(tmp_path):
    out = tmp_path / "results"; out.mkdir()
    sim = _sim_yaml(tmp_path, out)
    with pytest.raises(SystemExit):
        C.main([str(sim)])

def test_collect_refuses_on_fail(tmp_path, monkeypatch):
    out = tmp_path / "results"; (out / "c1" / "run_0001").mkdir(parents=True)
    (out / "c1" / "run_0001" / ".fluka_status").write_text("FLUKA_STATUS rc=1")
    _write_manifest(out)
    sim = _sim_yaml(tmp_path, out)
    called = {"analyze": False}
    monkeypatch.setattr(C, "analyze_phase", lambda p: called.__setitem__("analyze", True))
    with pytest.raises(SystemExit):
        C.main([str(sim), "--collect"])
    assert called["analyze"] is False

def test_collect_runs_when_all_done(tmp_path, monkeypatch):
    out = tmp_path / "results"; (out / "c1" / "run_0001").mkdir(parents=True)
    (out / "c1" / "run_0001" / ".fluka_status").write_text("FLUKA_STATUS rc=0")
    _write_manifest(out)
    sim = _sim_yaml(tmp_path, out)
    called = {"analyze": False}
    monkeypatch.setattr(C, "analyze_phase", lambda p: called.__setitem__("analyze", True))
    C.main([str(sim), "--collect"])
    assert called["analyze"] is True

def test_json_output(tmp_path, capsys):
    out = tmp_path / "results"; (out / "c1" / "run_0001").mkdir(parents=True)
    (out / "c1" / "run_0001" / ".fluka_status").write_text("FLUKA_STATUS rc=0")
    _write_manifest(out)
    sim = _sim_yaml(tmp_path, out)
    C.main([str(sim), "--json"])
    data = json.loads(capsys.readouterr().out)
    assert data[0]["state"] == "DONE"
