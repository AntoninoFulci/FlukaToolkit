import os
from dataclasses import dataclass
from pathlib import Path

from fluka.queue.backends.base import JobInfo, QueueBackend
from fluka.queue.backends.registry import new_backends
from fluka.queue.core import filesystem, fluka
from fluka.queue.core.config import SubmissionConfig


@dataclass(frozen=True, slots=True)
class PreparedJob:
    iteration: int
    job_dir: Path
    job_info: JobInfo


@dataclass(frozen=True, slots=True)
class SubmissionFailure:
    iteration: int
    error: RuntimeError


@dataclass(frozen=True, slots=True)
class SubmissionSummary:
    results: tuple[tuple[int, str], ...]
    failures: tuple[SubmissionFailure, ...] = ()


class SubmissionBatchError(RuntimeError):
    def __init__(self, summary: SubmissionSummary):
        self.summary = summary
        self.failures = summary.failures
        super().__init__(f"{len(self.failures)} job submission(s) failed")


def prepare_jobs(config: SubmissionConfig, fluka_path: str) -> list[PreparedJob]:
    if config.custom_exe is not None and not os.path.isfile(config.custom_exe):
        raise FileNotFoundError(f"Custom exe non trovato: {config.custom_exe}")

    base_name = Path(config.input).stem
    output_dir = Path(filesystem.setup_output_dir(base_name, config.output_dir))
    used_seeds = fluka.scan_existing_seeds(output_dir)
    prepared: list[PreparedJob] = []

    for iteration in range(1, config.njobs + 1):
        job_dir = Path(filesystem.setup_job_dir(str(output_dir), iteration, config.input))
        seed = fluka.allocate_seed(used_seeds)
        new_input = fluka.generate_input(
            base_name,
            iteration,
            str(job_dir),
            nprim=config.nprim,
            seed=seed,
        )
        input_file = str((job_dir / new_input).resolve()) if config.backend == "ts" else new_input
        job_info = JobInfo(
            input_file,
            iteration,
            fluka_path,
            config.custom_exe,
            use_dpm=config.use_dpm,
        )
        prepared.append(PreparedJob(iteration, job_dir, job_info))

    duplicates = fluka.find_duplicate_seeds(output_dir)
    if duplicates:
        details = "; ".join(
            f"{seed}: {', '.join(path.parent.name for path in files)}"
            for seed, files in sorted(duplicates.items())
        )
        raise RuntimeError(f"Seed RANDOMIZ duplicati rilevati: {details}")

    return prepared


def submit_prepared(
    config: SubmissionConfig,
    prepared: list[PreparedJob],
    backend: QueueBackend,
) -> SubmissionSummary:
    results: list[tuple[int, str]] = []
    failures: list[SubmissionFailure] = []

    for job in prepared:
        try:
            script_path = backend.generate_script(job.job_info, str(job.job_dir), config)
            result = backend.submit(script_path, job.job_info, config)
        except RuntimeError as error:
            failures.append(SubmissionFailure(job.iteration, error))
        else:
            results.append((job.iteration, result))

    summary = SubmissionSummary(tuple(results), tuple(failures))
    if failures:
        raise SubmissionBatchError(summary)
    return summary


def submit_jobs(
    config: SubmissionConfig,
    fluka_path: str,
    backends: dict[str, QueueBackend] | None = None,
) -> SubmissionSummary:
    available = new_backends() if backends is None else backends
    try:
        backend = available[config.backend]
    except KeyError as error:
        raise ValueError(f"Backend sconosciuto: {config.backend!r}") from error
    prepared = prepare_jobs(config, fluka_path)
    return submit_prepared(config, prepared, backend)
