from __future__ import annotations
import subprocess
from pathlib import Path
from typing import Optional

from .config import AnalysisConfig
from .reader import read_resnuclei_file
from .excel import write_activity_workbook


def resolve_rnc(directory: Path, unit: int, executable: str) -> Optional[Path]:
    """Return the .rnc file for `unit`, post-processing raw files if needed."""
    existing = sorted(directory.glob(f"*{unit}*.rnc"))
    if existing:
        if len(existing) > 1:
            names = ", ".join(p.name for p in existing)
            print(f"[warn] unit {unit}: multiple .rnc match ({names}); using {existing[0].name}")
        return existing[0]

    raw = sorted({*directory.glob(f"*.{unit}"), *directory.glob(f"fort.{unit}")})
    if not raw:
        return None

    output_name = f"merged_{unit}.rnc"
    stdin_input = "\n".join(str(f) for f in raw) + "\n\n" + output_name + "\n"
    result = subprocess.run(
        [executable],
        input=stdin_input,
        text=True,
        capture_output=True,
        cwd=directory,
    )
    (directory / f"{Path(executable).name}_{unit}.log").write_text(
        result.stdout + result.stderr
    )
    if result.returncode != 0:
        raise RuntimeError(
            f"{executable} failed for unit {unit} (exit {result.returncode}); "
            f"see {executable}_{unit}.log"
        )

    out_path = directory / output_name
    if not out_path.exists():
        raise RuntimeError(
            f"{executable} did not produce {output_name} for unit {unit}; "
            f"see {executable}_{unit}.log"
        )
    return out_path


def run_analysis(config: AnalysisConfig) -> None:
    directory = config.directory
    rows: list[dict] = []
    for unit in config.units:
        path = resolve_rnc(directory, unit, config.executable)
        if path is None:
            print(f"[warn] unit {unit}: no .rnc and no raw files, skipping")
            continue
        row = read_resnuclei_file(path, config.isotopes, {})
        if row is None:
            print(f"[warn] unit {unit}: {path.name} has no detector data, skipping")
            continue
        rows.append(row)

    if not rows:
        print("[analyze] no data found for any unit; nothing written")
        return

    output_path = directory / config.output
    write_activity_workbook(rows, config.isotopes, config.volume, output_path)
    print(f"[analyze] written {output_path}")
