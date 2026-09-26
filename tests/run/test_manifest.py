import json
from pathlib import Path

import pytest

from fluka.run.manifest import (
    Job,
    load_manifest,
    manifest_path_for,
    parse_job_id,
    record_job,
)


def _job(**kw):
    base = dict(
        combo="c1",
        run_idx=1,
        run_name="run_0001",
        run_dir="/out/c1/run_0001",
        backend="ts",
        job_id="7",
        input_file="simulation_0001.inp",
        submitted_at="2026-07-09T10:00:00",
        extra={},
    )
    base.update(kw)
    return Job(**base)


def test_manifest_path_for():
    assert manifest_path_for("/out") == Path("/out/.fluka_manifest.json")


def test_record_and_load_roundtrip(tmp_path):
    mp = manifest_path_for(tmp_path)
    record_job(mp, _job())
    jobs = load_manifest(mp)
    assert len(jobs) == 1
    assert jobs[0].job_id == "7" and jobs[0].combo == "c1"


def test_record_appends(tmp_path):
    mp = manifest_path_for(tmp_path)
    record_job(mp, _job(run_idx=1, run_name="run_0001", job_id="7"))
    record_job(mp, _job(run_idx=2, run_name="run_0002", job_id="8"))
    jobs = load_manifest(mp)
    assert [j.job_id for j in jobs] == ["7", "8"]


def test_load_missing_returns_empty(tmp_path):
    assert load_manifest(manifest_path_for(tmp_path)) == []


def test_manifest_is_valid_json(tmp_path):
    mp = manifest_path_for(tmp_path)
    record_job(mp, _job())
    data = json.loads(Path(mp).read_text())
    assert "jobs" in data and isinstance(data["jobs"], list)


@pytest.mark.parametrize(
    "backend,stdout,expected",
    [
        ("slurm", "Submitted batch job 12345", "12345"),
        ("lsf", "Job <678> is submitted to queue <normal>.", "678"),
        ("condor", "1 job(s) submitted to cluster 90.", "90"),
        ("ts", "42", "42"),
    ],
)
def test_parse_job_id(backend, stdout, expected):
    assert parse_job_id(backend, stdout) == expected


def test_parse_job_id_dry_run_passthrough():
    # dry-run outputs have no numeric id; return the raw string trimmed
    out = "[dry run] ts rfluka -M 1 x.inp"
    assert parse_job_id("ts", out) == out.strip()
