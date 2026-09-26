from __future__ import annotations
import getpass
import os
from pathlib import Path

# FlukaQueueSub (installed via submodule, editable)
from fluka.queue.backends.base import JobInfo
from fluka.queue.backends.registry import BACKEND_TYPES
from fluka.queue.core.config import SubmissionConfig

_DEFAULT_QUEUE = {"slurm": "production", "lsf": "normal", "condor": "vanilla"}


def _build_submission_config(
    backend_name: str, config, dry_run: bool
) -> SubmissionConfig:
    if backend_name not in BACKEND_TYPES:
        raise ValueError(f"Unknown backend: {backend_name!r}")
    ex = config.execution
    queue = ex.queue or _DEFAULT_QUEUE.get(backend_name)
    time = ex.condor_max_runtime if backend_name == "condor" else ex.time
    return SubmissionConfig(
        backend=backend_name,
        input=str(getattr(config.fluka, "input", "")),
        njobs=1,
        custom_exe=config.fluka.custom_executable,
        use_dpm=bool(getattr(config.fluka, "use_dpm", False)),
        dry_run=dry_run,
        queue=queue,
        mem=ex.mem,
        ntasks=ex.ntasks,
        nodes=ex.nodes,
        time=time,
        gres=ex.gres,
        farm_out=ex.farm_out,
        ncpu=ex.ncpu,
        disk=ex.disk,
    )


def manifest_extra(backend_name: str, config, run_dir, input_file) -> dict:
    """Build the per-backend `extra` payload stored in the run manifest."""
    if backend_name == "slurm":
        return {"farm_out": config.execution.farm_out,
                "user": getpass.getuser(),
                "job_name": input_file}
    if backend_name == "lsf":
        return {"job_dir": str(run_dir)}
    if backend_name == "condor":
        return {"output": "job_$(Cluster)_$(Process).out",
                "error": "job_$(Cluster)_$(Process).err",
                "log": "job_$(Cluster)_$(Process).log"}
    return {}


def submit_run(
    backend_name: str,
    config,
    run_dir: Path,
    inp_filename: str,
    iteration: int,
    fluka_bin: str,
    dry_run: bool,
) -> str:
    """Submit one run via a FlukaQueueSub backend. Returns the job-id string."""
    backend = BACKEND_TYPES[backend_name]()
    submission = _build_submission_config(backend_name, config, dry_run)
    backend.validate(submission)

    if backend_name == "ts":
        # TSBackend runs `ts rfluka -M 1 <input>` in the process CWD, so run it
        # from inside run_dir with an absolute input path (rfluka writes there).
        job_info = JobInfo(
            input_file=str((Path(run_dir) / inp_filename).resolve()),
            iteration=iteration,
            fluka_path=fluka_bin,
            custom_exe=config.fluka.custom_executable,
            use_dpm=config.fluka.use_dpm,
        )
        cwd = os.getcwd()
        os.chdir(run_dir)
        try:
            return backend.submit(None, job_info, submission)
        finally:
            os.chdir(cwd)

    job_info = JobInfo(
        input_file=inp_filename,
        iteration=iteration,
        fluka_path=fluka_bin,
        custom_exe=config.fluka.custom_executable,
        use_dpm=config.fluka.use_dpm,
    )
    script_path = backend.generate_script(
        job_info, str(Path(run_dir).resolve()), submission
    )
    return backend.submit(script_path, job_info, submission)
