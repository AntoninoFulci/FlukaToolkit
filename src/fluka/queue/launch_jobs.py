#!/usr/bin/env python3

import logging
import os
import sys
from argparse import ArgumentParser, RawTextHelpFormatter
from typing import TypedDict

from fluka.queue.backends.base import QueueBackend
from fluka.queue.backends.registry import new_backends
from fluka.queue.core import config, display, fluka
from fluka.queue.core.config import SubmissionConfig
from fluka.queue.service import (
    SubmissionBatchError,
    SubmissionSummary,
    submit_jobs,
)

BACKENDS = new_backends()

class _BenchmarkParams(TypedDict):
    njobs: int
    nprim: int
    use_priority_queue: bool


_BENCHMARK_MODES: dict[str, _BenchmarkParams] = {
    "quick":     {"njobs": 2,  "nprim": 100,  "use_priority_queue": True},
    "extensive": {"njobs": 5,  "nprim": 1000, "use_priority_queue": False},
}


def _apply_benchmark_overrides(
    args: SubmissionConfig, mode: str, backend: QueueBackend
) -> None:
    if mode not in _BENCHMARK_MODES:
        raise ValueError(
            f"Modalita' benchmark sconosciuta: {mode!r}. Disponibili: {sorted(_BENCHMARK_MODES)}"
        )
    params = _BENCHMARK_MODES[mode]
    args.njobs = params["njobs"]
    args.nprim = params["nprim"]
    if params["use_priority_queue"]:
        queue_name = getattr(args, "benchmark_priority_queue", None)
        if not queue_name:
            raise ValueError(
                "Campo 'benchmark_priority_queue' richiesto per benchmark quick"
            )
        backend.set_priority_queue(args, queue_name)


def _build_parser() -> ArgumentParser:
    parser = ArgumentParser(
        description=(
            "Lancia job FLUKA su diversi sistemi di code.\n"
            "\n"
            "Modalita' di utilizzo:\n"
            "\n"
            "  1) Subcomando diretto (CLI completo):\n"
            "       python launch_jobs.py <BACKEND> -f sim.inp -n 10 [opzioni]\n"
            "       python launch_jobs.py slurm -f sim.inp -n 5 -T 2-00:00:00\n"
            "       python launch_jobs.py condor -f sim.inp -n 20 -m 2000\n"
            "\n"
            "  2) File di configurazione YAML (singolo lancio):\n"
            "       python launch_jobs.py config.yaml\n"
            "       python launch_jobs.py JobConfigs/test_slurm.yaml\n"
            "\n"
            "  3) Cartella di file YAML (lancia tutti in sequenza):\n"
            "       python launch_jobs.py JobConfigs/\n"
            "\n"
            "  4) Modalita' benchmark (profili predefiniti):\n"
            "       python launch_jobs.py benchmark quick    config.yaml\n"
            "       python launch_jobs.py benchmark quick    JobConfigs/\n"
            "       python launch_jobs.py benchmark extensive config.yaml\n"
            "\n"
            "     quick:     2 job, 100 particelle, coda da benchmark_priority_queue\n"
            "     extensive: 5 job, 1000 particelle, coda invariata dal config\n"
            "\n"
            "Il file YAML deve contenere le stesse chiavi dei flag CLI.\n"
            "Esempio minimo (slurm):\n"
            "  backend: slurm\n"
            "  input: /path/to/sim.inp\n"
            "  njobs: 5\n"
            "  nprim: 10000        # opzionale\n"
            "  custom_exe: /path   # opzionale\n"
            "  benchmark_priority_queue: priority  # opzionale, richiesto per benchmark quick\n"
        ),
        formatter_class=RawTextHelpFormatter,
        epilog=(
            "Per la lista delle opzioni specifiche di ogni backend:\n"
            "  python launch_jobs.py slurm -h\n"
            "  python launch_jobs.py lsf -h\n"
            "  python launch_jobs.py condor -h\n"
            "  python launch_jobs.py ts -h\n"
        ),
    )
    subparsers = parser.add_subparsers(dest="backend", metavar="BACKEND")
    subparsers.required = True

    for name, backend in BACKENDS.items():
        sub = subparsers.add_parser(name, help=f"Invia job a {name.upper()}")
        sub.add_argument("-f", "--input",      type=str, required=True,
                         help="Percorso al file di input FLUKA (deve terminare in .inp)")
        sub.add_argument("-n", "--njobs",      type=int, required=True,
                         help="Numero di job indipendenti da lanciare (uno per seed casuale)")
        sub.add_argument("-c", "--custom-exe", type=str, default=None,
                         dest="custom_exe",
                         help="Percorso all'eseguibile FLUKA custom (passato come -e a rfluka); "
                              "se omesso usa l'eseguibile di default di FLUKA")
        sub.add_argument("-w", "--dry-run",    action="store_true",
                         dest="dry_run",
                         help="Modalita' dry-run: costruisce gli script e mostra i comandi "
                              "senza inviare alcun job al sistema di code")
        sub.add_argument("-d", "--output-dir", type=str, default=None,
                         dest="output_dir",
                         help="Directory radice dove creare le sottocartelle dei job "
                              "(default: nome del file di input senza estensione)")
        sub.add_argument("-N", "--nprim", type=int, default=None,
                         dest="nprim",
                         help="Numero di particelle primarie per job: sovrascrive la card "
                              "START nel file .inp rispettando il formato colonnare FLUKA; "
                              "se omesso il valore nel .inp rimane invariato")
        backend.add_args(sub)

    return parser


def _log_summary(summary: SubmissionSummary) -> None:
    for iteration, result in summary.results:
        logging.info("Job %d: %s", iteration, result)


def _log_submission_batch(error: SubmissionBatchError) -> None:
    _log_summary(error.summary)
    for failure in error.failures:
        logging.error("Job %d fallito: %s", failure.iteration, failure.error)


def run_submission(args: SubmissionConfig) -> SubmissionSummary | None:
    if not args.input.endswith(".inp"):
        raise ValueError("Input file must end with .inp")

    fluka_path, fluka_folder = fluka.detect_fluka_path()
    try:
        backend = BACKENDS[args.backend]
    except KeyError as error:
        raise ValueError(f"Backend sconosciuto: {args.backend!r}") from error

    backend.validate(args)

    C = display.COLORS
    common_rows = [
        ["Flag", "Parametro", "Valore"],
        ["-f", f"{C['R']}Input file{C['RE']}",  f"{C['M']}{args.input}{C['RE']}"],
        ["-n", f"{C['R']}Numero job{C['RE']}",  f"{C['M']}{args.njobs}{C['RE']}"],
        ["-c", f"{C['M']}Custom exe{C['RE']}",  f"{C['M']}{args.custom_exe or 'None'}{C['RE']}"],
        ["-d", f"{C['B']}Output dir{C['RE']}",  f"{C['B']}{args.output_dir or 'Default'}{C['RE']}"],
        ["-N", f"{C['C']}N. primarie{C['RE']}", f"{C['C']}{args.nprim if args.nprim is not None else 'dal file'}{C['RE']}"],
        ["-w", f"{C['Y']}Dry run{C['RE']}",     f"{C['Y']}{args.dry_run}{C['RE']}"],
    ]
    display.print_table(common_rows + backend.table_rows(args, fluka_path, fluka_folder))

    if not display.confirm():
        logging.info("Lancio annullato.")
        return None

    summary = submit_jobs(args, fluka_path, BACKENDS)
    _log_summary(summary)
    return summary


def run_folder(folder: str) -> int:
    yaml_files = sorted(
        f for f in os.listdir(folder) if f.endswith((".yaml", ".yml"))
    )
    yaml_paths = [os.path.join(folder, f) for f in yaml_files]

    if not yaml_paths:
        logging.warning("Nessun file YAML trovato in %r", folder)
        return 0

    configs = []
    for path in yaml_paths:
        try:
            cfg = config.load_yaml_config(path, BACKENDS)
            BACKENDS[cfg.backend].validate(cfg)
            configs.append((path, cfg))
        except (OSError, ValueError, RuntimeError) as e:
            logging.error("File %r non valido: %s", path, e)

    if not configs:
        logging.error("Nessuna configurazione valida trovata.")
        return 0

    C = display.COLORS
    rows = [["File", "Backend", "N. job"]]
    for path, cfg in configs:
        rows.append([
            os.path.basename(path),
            f"{C['M']}{cfg.backend}{C['RE']}",
            f"{C['M']}{cfg.njobs}{C['RE']}",
        ])
    display.print_table(rows)

    if not display.confirm(f"Procedere con {len(configs)} lanci? (yes/no): "):
        logging.info("Lancio annullato.")
        return 0

    fluka_path, _ = fluka.detect_fluka_path()
    failures = 0
    for path, cfg in configs:
        try:
            logging.info("Avvio: %s", os.path.basename(path))
            summary = submit_jobs(cfg, fluka_path, BACKENDS)
            _log_summary(summary)
        except SubmissionBatchError as e:
            _log_submission_batch(e)
            failures += 1
        except (OSError, ValueError, RuntimeError) as e:
            logging.error("Errore in %r: %s", path, e)
            failures += 1
    return failures


def _has_start_card(inp_path: str) -> bool:
    """Return True if the FLUKA input file contains a START card."""
    with open(inp_path) as f:
        return any(line.startswith("START") for line in f)


def run_benchmark(mode: str, target: str) -> int:
    C = display.COLORS

    if os.path.isdir(target):
        yaml_files = sorted(f for f in os.listdir(target) if f.endswith((".yaml", ".yml")))
        yaml_paths = [os.path.join(target, f) for f in yaml_files]

        if not yaml_paths:
            logging.warning("Nessun file YAML trovato in %r", target)
            return 0

        configs = []
        for path in yaml_paths:
            try:
                cfg = config.load_yaml_config(path, BACKENDS)
                BACKENDS[cfg.backend].validate(cfg)
                configs.append((path, cfg))
            except (OSError, ValueError, RuntimeError) as e:
                logging.error("File %r non valido: %s", path, e)

        if not configs:
            logging.error("Nessuna configurazione valida trovata.")
            return 0

        for path, cfg in configs:
            _apply_benchmark_overrides(cfg, mode, BACKENDS[cfg.backend])

        params = _BENCHMARK_MODES[mode]
        print(
            f"\n[BENCHMARK MODE: {mode} — "
            f"njobs={params['njobs']}, nprim={params['nprim']}"
            + (", priority_queue override active" if params["use_priority_queue"] else "")
            + "]"
        )
        rows = [["File", "Backend", "N. job (benchmark)"]]
        for path, cfg in configs:
            rows.append([
                os.path.basename(path),
                f"{C['M']}{cfg.backend}{C['RE']}",
                f"{C['M']}{cfg.njobs}{C['RE']}",
            ])
        display.print_table(rows)

        if not display.confirm(f"Procedere con {len(configs)} lanci benchmark? (yes/no): "):
            logging.info("Lancio annullato.")
            return 0

        fluka_path, _ = fluka.detect_fluka_path()
        failures = 0
        for path, cfg in configs:
            try:
                logging.info("Avvio benchmark: %s", os.path.basename(path))
                if cfg.nprim is not None and not _has_start_card(cfg.input):
                    logging.warning(
                        "Nessuna card START in %r — nprim ignorato per questo lancio.", cfg.input
                    )
                    cfg.nprim = None
                summary = submit_jobs(cfg, fluka_path, BACKENDS)
                _log_summary(summary)
            except SubmissionBatchError as e:
                _log_submission_batch(e)
                failures += 1
            except (OSError, ValueError, RuntimeError) as e:
                logging.error("Errore in %r: %s", path, e)
                failures += 1
        return failures

    else:
        cfg = config.load_yaml_config(target, BACKENDS)

        backend = BACKENDS[cfg.backend]
        backend.validate(cfg)
        _apply_benchmark_overrides(cfg, mode, backend)

        if cfg.nprim is not None and not _has_start_card(cfg.input):
            logging.warning(
                "Nessuna card START in %r — nprim ignorato per questo lancio.", cfg.input
            )
            cfg.nprim = None

        params = _BENCHMARK_MODES[mode]
        print(
            f"\n[BENCHMARK MODE: {mode} — "
            f"njobs={params['njobs']}, nprim={params['nprim']}"
            + (", priority_queue override active" if params["use_priority_queue"] else "")
            + "]"
        )
        if not display.confirm("Procedere con lancio benchmark? (yes/no): "):
            logging.info("Lancio annullato.")
            return 0
        fluka_path, _ = fluka.detect_fluka_path()
        summary = submit_jobs(cfg, fluka_path, BACKENDS)
        _log_summary(summary)
        return 0


def main() -> None:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(levelname)s - %(message)s",
    )
    if len(sys.argv) > 1 and sys.argv[1] == "benchmark":
        if len(sys.argv) != 4:
            print("Utilizzo: launch_jobs.py benchmark <quick|extensive> <config.yaml|cartella/>")
            sys.exit(1)
        if sys.argv[2] not in _BENCHMARK_MODES:
            print(f"Modalita' sconosciuta: {sys.argv[2]!r}. Disponibili: {sorted(_BENCHMARK_MODES)}")
            sys.exit(1)
        try:
            failures = run_benchmark(sys.argv[2], sys.argv[3])
        except SubmissionBatchError as e:
            _log_submission_batch(e)
            sys.exit(1)
        except (OSError, ValueError, RuntimeError) as e:
            logging.error(str(e))
            sys.exit(1)
        if failures:
            sys.exit(1)
        return
    if len(sys.argv) > 1:
        first_arg = sys.argv[1]
        if first_arg.endswith((".yaml", ".yml")) and not os.path.isdir(first_arg):
            try:
                args = config.load_yaml_config(first_arg, BACKENDS)
            except (FileNotFoundError, ValueError) as e:
                logging.error(str(e))
                sys.exit(1)
            try:
                run_submission(args)
            except SubmissionBatchError as e:
                _log_submission_batch(e)
                sys.exit(1)
            except (OSError, ValueError, RuntimeError) as e:
                logging.error(str(e))
                sys.exit(1)
            return
        if os.path.isdir(first_arg):
            try:
                failures = run_folder(first_arg)
            except (OSError, ValueError, RuntimeError) as e:
                logging.error(str(e))
                sys.exit(1)
            if failures:
                sys.exit(1)
            return
    parser = _build_parser()
    namespace = parser.parse_args()
    try:
        run_submission(SubmissionConfig.from_mapping(vars(namespace)))
    except SubmissionBatchError as e:
        _log_submission_batch(e)
        sys.exit(1)
    except (OSError, ValueError, RuntimeError) as e:
        logging.error(str(e))
        sys.exit(1)


if __name__ == "__main__":
    main()
