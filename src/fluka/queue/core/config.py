from argparse import ArgumentParser
from collections.abc import Mapping
from dataclasses import dataclass, fields
from typing import Any

import yaml

from fluka.queue.backends.base import QueueBackend

# general-section keys (see fluka.run.simconfig.GENERAL_KEYS) that are mapped
# to typed fields explicitly below rather than blindly overlaid onto the
# backend arg defaults -- this keeps e.g. the merged view's "output" (the
# results directory) from clobbering HTCondor's own "--output" arg (the job
# stdout filename pattern), which happens to share the same dest name.
_GENERAL_ONLY_KEYS = frozenset(
    {
        "input",
        "backend",
        "output",
        "primaries",
        "use_dpm",
        "custom_executable",
        "rfluka_path",
        "njobs",
        "_config_dir",
        "_general_output",
    }
)


@dataclass(slots=True)
class SubmissionConfig:
    backend: str
    input: str
    njobs: int
    custom_exe: str | None = None
    use_dpm: bool = False
    dry_run: bool = False
    output_dir: str | None = None
    nprim: int | None = None
    queue: str | None = None
    mem: str = "1500"
    ntasks: int = 1
    nodes: int = 1
    time: str | int = "1-00:00:00"
    gres: str = "disk:1G"
    farm_out: str = "/farm_out"
    ncpu: int = 1
    disk: int = 100000
    transfer_files: str = "yes"
    stdout: str = "job_$(Cluster)_$(Process).out"
    stderr: str = "job_$(Cluster)_$(Process).err"
    log: str = "job_$(Cluster)_$(Process).log"
    benchmark_priority_queue: str | None = None

    @classmethod
    def from_mapping(cls, values: Mapping[str, Any]) -> "SubmissionConfig":
        normalized = dict(values)
        if "output" in normalized and "stdout" not in normalized:
            normalized["stdout"] = normalized["output"]
        if "error" in normalized and "stderr" not in normalized:
            normalized["stderr"] = normalized["error"]
        known = {field.name for field in fields(cls)}
        return cls(**{key: value for key, value in normalized.items() if key in known})


def _parser_defaults(backend: QueueBackend) -> dict[str, Any]:
    parser = ArgumentParser()
    parser.add_argument("--input", dest="input", default=None)
    parser.add_argument("--njobs", dest="njobs", type=int, default=None)
    parser.add_argument("--custom-exe", dest="custom_exe", default=None)
    parser.add_argument("--dpm", dest="use_dpm", action="store_true", default=False)
    parser.add_argument("--dry-run", dest="dry_run", action="store_true", default=False)
    parser.add_argument("--output-dir", dest="output_dir", default=None)
    parser.add_argument("--nprim", dest="nprim", type=int, default=None)
    backend.add_args(parser)
    return vars(parser.parse_args([]))


def _validate_submission_values(values: dict[str, Any], source: str) -> None:
    if values.get("njobs") is not None:
        try:
            values["njobs"] = int(values["njobs"])
        except (ValueError, TypeError):
            raise ValueError(f"'njobs' deve essere un intero, trovato: {values.get('njobs')!r}")
        if values["njobs"] < 1:
            raise ValueError(f"'njobs' deve essere >= 1, trovato: {values['njobs']}")

    if values.get("input") is None:
        raise ValueError(f"Campo 'input' mancante {source}")
    if not str(values["input"]).endswith(".inp"):
        raise ValueError(f"Il file di input deve terminare con .inp: {values['input']!r}")
    if values.get("njobs") is None:
        raise ValueError(f"Campo 'njobs' mancante {source}")
    if values.get("use_dpm") and values.get("custom_exe"):
        raise ValueError("use_dpm and custom_exe are mutually exclusive: set only one.")


def load_submission_config(path: str, backends: dict[str, QueueBackend]) -> SubmissionConfig:
    with open(path) as f:
        data = yaml.safe_load(f)

    if not isinstance(data, dict):
        raise ValueError(f"Il file YAML deve contenere un dizionario: {path!r}")

    backend_name = data.get("backend")
    if not backend_name:
        raise ValueError(f"Campo 'backend' mancante in {path!r}")
    if backend_name not in backends:
        raise ValueError(f"Backend sconosciuto {backend_name!r}. Disponibili: {sorted(backends)}")

    backend = backends[backend_name]

    defaults = _parser_defaults(backend)
    legacy_values = dict(data)
    if "output" in legacy_values:
        legacy_values["stdout"] = legacy_values.pop("output")
    if "error" in legacy_values:
        legacy_values["stderr"] = legacy_values.pop("error")
    defaults.update(legacy_values)
    defaults["backend"] = backend_name
    _validate_submission_values(defaults, f"in {path!r}")
    return SubmissionConfig.from_mapping(defaults)


def submission_config_from_view(view: dict, backends: dict[str, QueueBackend]) -> SubmissionConfig:
    """Build typed submission settings from a merged ``sim.yaml`` view.

    backend/input come from general (via resolve); njobs and the batch-resource
    fields (mem/time/ntasks/nodes/gres/ncpu/disk/queue/farm_out/...) come from
    submit. dry_run is always False here -- the submit path is a real launch,
    never a dry run.
    """
    backend_name = view.get("backend")
    if not backend_name:
        raise ValueError("Campo 'backend' mancante nella configurazione")
    if backend_name not in backends:
        raise ValueError(f"Backend sconosciuto {backend_name!r}. Disponibili: {sorted(backends)}")

    backend = backends[backend_name]

    defaults = _parser_defaults(backend)
    normalized_view = dict(view)
    if "error" in normalized_view and "stderr" not in normalized_view:
        normalized_view["stderr"] = normalized_view["error"]
    # overlay backend arg defaults with any matching keys present in the view
    # (mem/time/ntasks/nodes/gres/ncpu/disk/queue/farm_out, ...), skipping the
    # general-mapped keys that are set explicitly below.
    for key in defaults:
        if key in normalized_view and key not in _GENERAL_ONLY_KEYS:
            defaults[key] = normalized_view[key]

    defaults["backend"] = backend_name
    defaults["input"] = view.get("input")
    defaults["dry_run"] = False
    defaults["output_dir"] = view.get("output")
    defaults["custom_exe"] = view.get("custom_executable")
    defaults["use_dpm"] = bool(view.get("use_dpm", False))
    if view.get("primaries") is not None:
        defaults["nprim"] = view["primaries"]

    defaults["njobs"] = view.get("njobs")
    if backend_name == "condor" and view.get("condor_max_runtime") is not None:
        defaults["time"] = view["condor_max_runtime"]

    _validate_submission_values(defaults, "nella configurazione")
    return SubmissionConfig.from_mapping(defaults)


# Transitional internal names used by current CLI modules.
load_yaml_config = load_submission_config
build_submit_args = submission_config_from_view
