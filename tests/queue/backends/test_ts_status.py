import subprocess
from pathlib import Path

from fluka.queue.backends.ts import TSBackend
from fluka.queue.core.config import SubmissionConfig
from fluka.run import status as S
from fluka.run.manifest import Job


def _job(run_dir):
    return Job(
        combo="c1",
        run_idx=1,
        run_name="run_0001",
        run_dir=str(run_dir),
        backend="ts",
        job_id="5",
        input_file="s.inp",
        submitted_at="t",
        extra={},
    )


def test_sentinel_path(tmp_path):
    b = TSBackend()
    assert Path(b._sentinel_path(_job(tmp_path))) == Path(tmp_path) / ".fluka_status"


def test_queue_state_running(monkeypatch):
    def fake_run(cmd, **kw):
        return subprocess.CompletedProcess(cmd, 0, stdout="running", stderr="")

    monkeypatch.setattr(subprocess, "run", fake_run)
    assert TSBackend()._queue_state(_job("/x")) in (S.RUNNING, S.PENDING)


def test_queue_state_absent(monkeypatch):
    def fake_run(cmd, **kw):
        return subprocess.CompletedProcess(cmd, 1, stdout="", stderr="unknown jobid")

    monkeypatch.setattr(subprocess, "run", fake_run)
    assert TSBackend()._queue_state(_job("/x")) is None


def test_submit_wraps_sentinel(monkeypatch):
    captured = {}

    def fake_run(cmd, **kw):
        captured["cmd"] = cmd
        return subprocess.CompletedProcess(cmd, 0, stdout="9", stderr="")

    monkeypatch.setattr(subprocess, "run", fake_run)
    from fluka.queue.backends.base import JobInfo

    ji = JobInfo(input_file="s.inp", iteration=1, fluka_path="/f", custom_exe=None)
    config = SubmissionConfig(backend="ts", input="s.inp", njobs=1)
    TSBackend().submit(None, ji, config)
    joined = " ".join(captured["cmd"])
    assert "FLUKA_STATUS rc=$rc" in joined and ".fluka_status" in joined
