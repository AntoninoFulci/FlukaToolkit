from pathlib import Path
import subprocess
from fluka.queue.backends.lsf import LSFBackend
from fluka.queue.backends.base import JobInfo
from fluka.queue.core.config import SubmissionConfig
from fluka.run.manifest import Job
from fluka.run import status as S


def _args():
    return SubmissionConfig(
        backend="lsf", input="s.inp", njobs=1, dry_run=True,
        queue="normal", mem="1500", ntasks=1, time="1-00:00:00",
    )

def _job(run_dir="/o/c1/run_0001"):
    return Job(combo="c1", run_idx=1, run_name="run_0001", run_dir=run_dir,
               backend="lsf", job_id="55", input_file="s.inp", submitted_at="t", extra={})

def test_template_writes_sentinel(tmp_path):
    ji = JobInfo(input_file="s.inp", iteration=1, fluka_path="/f", custom_exe=None)
    content = Path(LSFBackend().generate_script(ji, str(tmp_path), _args())).read_text()
    assert "FLUKA_STATUS rc=$rc" in content and ".fluka_status" in content

def test_sentinel_path(tmp_path):
    assert Path(LSFBackend()._sentinel_path(_job(tmp_path))) == Path(tmp_path) / ".fluka_status"

def test_queue_state_running(monkeypatch):
    def fake_run(cmd, **kw):
        return subprocess.CompletedProcess(cmd, 0, stdout="RUN\n", stderr="")
    monkeypatch.setattr(subprocess, "run", fake_run)
    assert LSFBackend()._queue_state(_job()) == S.RUNNING

def test_queue_state_pending(monkeypatch):
    def fake_run(cmd, **kw):
        return subprocess.CompletedProcess(cmd, 0, stdout="PEND\n", stderr="")
    monkeypatch.setattr(subprocess, "run", fake_run)
    assert LSFBackend()._queue_state(_job()) == S.PENDING

def test_queue_state_absent(monkeypatch):
    def fake_run(cmd, **kw):
        return subprocess.CompletedProcess(cmd, 255, stdout="", stderr="Job <55> is not found")
    monkeypatch.setattr(subprocess, "run", fake_run)
    assert LSFBackend()._queue_state(_job()) is None

def test_queue_state_missing_binary(monkeypatch):
    def fake_run(cmd, **kw):
        raise FileNotFoundError("bjobs not found")
    monkeypatch.setattr(subprocess, "run", fake_run)
    assert LSFBackend()._queue_state(_job()) is None
