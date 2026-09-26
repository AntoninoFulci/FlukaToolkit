from __future__ import annotations

import json
import re
from dataclasses import asdict, dataclass, field
from pathlib import Path


@dataclass
class Job:
    combo: str
    run_idx: int
    run_name: str
    run_dir: str
    backend: str
    job_id: str
    input_file: str
    submitted_at: str
    extra: dict = field(default_factory=dict)


def manifest_path_for(output_dir: str | Path) -> Path:
    return Path(output_dir) / ".fluka_manifest.json"


def load_manifest(manifest_path: str | Path) -> list[Job]:
    p = Path(manifest_path)
    if not p.exists():
        return []
    data = json.loads(p.read_text() or "{}")
    return [Job(**j) for j in data.get("jobs", [])]


def record_job(manifest_path: str | Path, job: Job) -> None:
    p = Path(manifest_path)
    jobs = load_manifest(p)
    jobs.append(job)
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps({"jobs": [asdict(j) for j in jobs]}, indent=2))


_ID_PATTERNS = {
    "slurm": re.compile(r"Submitted batch job (\d+)"),
    "lsf": re.compile(r"Job <(\d+)>"),
    "condor": re.compile(r"cluster (\d+)"),
    "ts": re.compile(r"^(\d+)$"),
}


def parse_job_id(backend: str, submit_stdout: str) -> str:
    s = (submit_stdout or "").strip()
    pat = _ID_PATTERNS.get(backend)
    if pat:
        m = pat.search(s)
        if m:
            return m.group(1)
    return s
