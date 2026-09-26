import re as _re
from abc import ABC, abstractmethod
from argparse import ArgumentParser
from dataclasses import dataclass
from pathlib import Path as _Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from fluka.queue.core.config import SubmissionConfig

_SENTINEL_RE = _re.compile(r"FLUKA_STATUS rc=(-?\d+)")


def read_sentinel(path) -> tuple[bool, int] | None:
    """Parse a 'FLUKA_STATUS rc=N' sentinel file. Return (True, rc) or None."""
    if path is None:
        return None
    p = _Path(path)
    if not p.exists():
        return None
    m = _SENTINEL_RE.search(p.read_text())
    return (True, int(m.group(1))) if m else None


@dataclass
class JobInfo:
    input_file: str
    iteration: int
    fluka_path: str
    custom_exe: str | None
    use_dpm: bool = False


class QueueBackend(ABC):
    def job_state(self, job, args=None) -> tuple[str, str]:
        from fluka.run.status import DONE, FAIL, PENDING, RUNNING, UNKNOWN  # noqa: F401

        qs = self._queue_state(job)
        if qs is not None:
            return qs, "in queue"
        sent = read_sentinel(self._sentinel_path(job))
        if sent is None:
            return UNKNOWN, "not in queue, no sentinel"
        _, rc = sent
        return (DONE, f"rc={rc}") if rc == 0 else (FAIL, f"rc={rc}")

    def _queue_state(self, job):
        return None

    def _sentinel_path(self, job):
        return None

    @abstractmethod
    def add_args(self, parser: ArgumentParser) -> None:
        """Aggiunge gli argomenti specifici del backend al subparser."""

    @abstractmethod
    def validate(self, args: "SubmissionConfig") -> None:
        """Valida gli argomenti. Lancia ValueError se non validi."""

    @abstractmethod
    def generate_script(
        self, job_info: JobInfo, job_dir: str, args: "SubmissionConfig"
    ) -> str | None:
        """Genera lo script di job. Restituisce il path o None (es. Task Spooler)."""

    @abstractmethod
    def submit(self, script_path: str | None, job_info: JobInfo, args: "SubmissionConfig") -> str:
        """Invia il job. Restituisce una stringa descrittiva (job ID, ecc.)."""

    @abstractmethod
    def table_rows(
        self, args: "SubmissionConfig", fluka_path: str, fluka_folder: str
    ) -> list[list[str]]:
        """Restituisce le righe specifiche del backend per la tabella di riepilogo."""

    @abstractmethod
    def set_priority_queue(self, args: "SubmissionConfig", queue_name: str) -> None:
        """Sovrascrive il campo queue/partition in args per la modalita' benchmark rapida."""
