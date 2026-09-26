import pytest
from unittest.mock import patch
from fluka.queue.backends.ts import TSBackend
from fluka.queue.backends.base import JobInfo
from fluka.queue.core.config import SubmissionConfig

BACKEND = TSBackend()

def make_args(**kwargs):
    defaults = dict(
        backend="ts", input="sim.inp", njobs=1,
        dry_run=False, custom_exe=None,
    )
    defaults.update(kwargs)
    return SubmissionConfig(**defaults)

def test_validate_does_not_raise():
    BACKEND.validate(make_args())

def test_generate_script_returns_none(tmp_path):
    job_info = JobInfo("sim_0001.inp", 1, "/usr/local/fluka/bin", None)
    result = BACKEND.generate_script(job_info, str(tmp_path), make_args())
    assert result is None

def test_submit_dry_run_contains_ts_and_rfluka():
    job_info = JobInfo("sim_0001.inp", 1, "/usr/local/fluka/bin", None)
    result = BACKEND.submit(None, job_info, make_args(dry_run=True))
    assert "dry run" in result.lower()
    assert "ts" in result
    assert "rfluka" in result
    assert "sim_0001.inp" in result
    assert "rc=$?" in result
    assert "FLUKA_STATUS rc=$rc" in result
    assert 'exit "$rc"' in result

def test_submit_dry_run_with_custom_exe():
    job_info = JobInfo("sim_0001.inp", 1, "/usr/local/fluka/bin", "/path/to/exe")
    result = BACKEND.submit(None, job_info, make_args(dry_run=True, custom_exe="/path/to/exe"))
    assert "-e /path/to/exe" in result


def test_submit_absolute_input_runs_from_its_job_directory(tmp_path):
    """rfluka writes outputs in cwd, so TS must enter input's job directory."""
    job_dir = tmp_path / "job with space"
    job_dir.mkdir()
    job_info = JobInfo(str(job_dir / "sim_0001.inp"), 1, "/usr/local/fluka/bin", None)
    result = BACKEND.submit(None, job_info, make_args(dry_run=True))
    assert f"cd '{job_dir}'" in result
    assert "sim_0001.inp" in result

def test_submit_calls_ts():
    job_info = JobInfo("sim_0001.inp", 1, "/usr/local/fluka/bin", None)
    with patch("subprocess.run") as mock_run:
        mock_run.return_value.returncode = 0
        mock_run.return_value.stdout = "3"
        result = BACKEND.submit(None, job_info, make_args(dry_run=False))
    assert "3" in result
    assert mock_run.call_args[0][0][0] == "ts"
    assert "rfluka" in " ".join(mock_run.call_args[0][0])

def test_submit_raises_on_failure():
    job_info = JobInfo("sim_0001.inp", 1, "/usr/local/fluka/bin", None)
    with patch("subprocess.run") as mock_run:
        mock_run.return_value.returncode = 1
        mock_run.return_value.stderr = "ts: command not found"
        with pytest.raises(RuntimeError, match="ts: command not found"):
            BACKEND.submit(None, job_info, make_args(dry_run=False))

def test_table_rows_returns_list():
    rows = BACKEND.table_rows(make_args(), "/bin", "/fluka")
    assert isinstance(rows, list)
