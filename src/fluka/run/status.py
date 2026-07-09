from __future__ import annotations
from dataclasses import dataclass

PENDING = "PENDING"
RUNNING = "RUNNING"
DONE = "DONE"
FAIL = "FAIL"
UNKNOWN = "UNKNOWN"

_TERMINAL = {DONE, FAIL}
_ORDER = [RUNNING, PENDING, UNKNOWN, FAIL, DONE]


@dataclass
class JobStatus:
    job: "object"
    state: str
    detail: str


def resolve_all(jobs, backends, args=None) -> list[JobStatus]:
    out = []
    for job in jobs:
        backend = backends[job.backend]
        state, detail = backend.job_state(job, args)
        out.append(JobStatus(job=job, state=state, detail=detail))
    return out


def all_terminal(statuses) -> bool:
    return all(s.state in _TERMINAL for s in statuses)


def summary_counts(statuses) -> dict:
    counts = {k: 0 for k in _ORDER}
    for s in statuses:
        counts[s.state] = counts.get(s.state, 0) + 1
    return counts
