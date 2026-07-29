from argparse import ArgumentParser, Namespace

import yaml

from fluka.queue.backends.base import QueueBackend

# general-section keys (see fluka.run.simconfig.GENERAL_KEYS) that are mapped
# to Namespace fields explicitly below rather than blindly overlaid onto the
# backend arg defaults -- this keeps e.g. the merged view's "output" (the
# results directory) from clobbering HTCondor's own "--output" arg (the job
# stdout filename pattern), which happens to share the same dest name.
_GENERAL_ONLY_KEYS = frozenset({
    "input", "backend", "output", "primaries", "use_dpm",
    "custom_executable", "rfluka_path", "njobs",
    "_config_dir", "_general_output",
})


def load_yaml_config(path: str, backends: dict[str, QueueBackend]) -> Namespace:
    with open(path) as f:
        data = yaml.safe_load(f)

    if not isinstance(data, dict):
        raise ValueError(f"Il file YAML deve contenere un dizionario: {path!r}")

    backend_name = data.get("backend")
    if not backend_name:
        raise ValueError(f"Campo 'backend' mancante in {path!r}")
    if backend_name not in backends:
        raise ValueError(
            f"Backend sconosciuto {backend_name!r}. Disponibili: {sorted(backends)}"
        )

    backend = backends[backend_name]

    # Costruisce un parser temporaneo per estrarre i default del backend
    parser = ArgumentParser()
    parser.add_argument("--input",      dest="input",      default=None)
    parser.add_argument("--njobs",      dest="njobs",      type=int, default=None)
    parser.add_argument("--custom-exe", dest="custom_exe", default=None)
    parser.add_argument("--dpm", dest="use_dpm", action="store_true", default=False)
    parser.add_argument("--dry-run",    dest="dry_run",    action="store_true", default=False)
    parser.add_argument("--output-dir", dest="output_dir", default=None)
    parser.add_argument("--nprim",      dest="nprim",      type=int, default=None)
    backend.add_args(parser)

    defaults = vars(parser.parse_args([]))
    defaults.update(data)
    defaults["backend"] = backend_name

    if defaults.get("njobs") is not None:
        try:
            defaults["njobs"] = int(defaults["njobs"])
        except (ValueError, TypeError):
            raise ValueError(f"'njobs' deve essere un intero, trovato: {defaults.get('njobs')!r}")
        if defaults["njobs"] < 1:
            raise ValueError(f"'njobs' deve essere >= 1, trovato: {defaults['njobs']}")

    if defaults.get("input") is None:
        raise ValueError(f"Campo 'input' mancante in {path!r}")
    if not str(defaults["input"]).endswith(".inp"):
        raise ValueError(f"Il file di input deve terminare con .inp: {defaults['input']!r}")
    if defaults.get("njobs") is None:
        raise ValueError(f"Campo 'njobs' mancante in {path!r}")

    if defaults.get("use_dpm") and defaults.get("custom_exe"):
        raise ValueError(
            "use_dpm and custom_exe are mutually exclusive: set only one."
        )

    return Namespace(**defaults)


def build_submit_args(view: dict, backends: dict[str, QueueBackend]) -> Namespace:
    """Turn a merged v2 view (fluka.run.simconfig.resolve(path, "submit")) into
    the same Namespace shape load_yaml_config produces, so run_from_args keeps
    working unchanged.

    backend/input come from general (via resolve); njobs and the batch-resource
    fields (mem/time/ntasks/nodes/gres/ncpu/disk/queue/farm_out/...) come from
    submit. dry_run is always False here -- the submit path is a real launch,
    never a dry run.
    """
    backend_name = view.get("backend")
    if not backend_name:
        raise ValueError("Campo 'backend' mancante nella configurazione")
    if backend_name not in backends:
        raise ValueError(
            f"Backend sconosciuto {backend_name!r}. Disponibili: {sorted(backends)}"
        )

    backend = backends[backend_name]

    # Costruisce un parser temporaneo per estrarre i default del backend
    parser = ArgumentParser()
    parser.add_argument("--input",      dest="input",      default=None)
    parser.add_argument("--njobs",      dest="njobs",      type=int, default=None)
    parser.add_argument("--custom-exe", dest="custom_exe", default=None)
    parser.add_argument("--dpm", dest="use_dpm", action="store_true", default=False)
    parser.add_argument("--dry-run",    dest="dry_run",    action="store_true", default=False)
    parser.add_argument("--output-dir", dest="output_dir", default=None)
    parser.add_argument("--nprim",      dest="nprim",      type=int, default=None)
    backend.add_args(parser)

    defaults = vars(parser.parse_args([]))
    # overlay backend arg defaults with any matching keys present in the view
    # (mem/time/ntasks/nodes/gres/ncpu/disk/queue/farm_out, ...), skipping the
    # general-mapped keys that are set explicitly below.
    for key in defaults:
        if key in view and key not in _GENERAL_ONLY_KEYS:
            defaults[key] = view[key]

    defaults["backend"] = backend_name
    defaults["input"] = view.get("input")
    defaults["dry_run"] = False
    defaults["output_dir"] = view.get("output")
    defaults["custom_exe"] = view.get("custom_executable")
    defaults["use_dpm"] = bool(view.get("use_dpm", False))
    if view.get("primaries") is not None:
        defaults["nprim"] = view["primaries"]

    njobs = view.get("njobs")
    if njobs is None:
        raise ValueError("Campo 'njobs' mancante nella sezione submit")
    try:
        njobs = int(njobs)
    except (ValueError, TypeError):
        raise ValueError(f"'njobs' deve essere un intero, trovato: {njobs!r}")
    if njobs < 1:
        raise ValueError(f"'njobs' deve essere >= 1, trovato: {njobs}")
    defaults["njobs"] = njobs

    if defaults.get("input") is None:
        raise ValueError("Campo 'input' mancante nella configurazione")
    if not str(defaults["input"]).endswith(".inp"):
        raise ValueError(f"Il file di input deve terminare con .inp: {defaults['input']!r}")

    if defaults.get("use_dpm") and defaults.get("custom_exe"):
        raise ValueError(
            "use_dpm and custom_exe are mutually exclusive: set only one."
        )

    return Namespace(**defaults)
