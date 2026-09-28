from __future__ import annotations

from pathlib import Path

import pandas as pd

from .physics import isotope_symbol
from .reader import AnalysisRow


def write_activity_workbook(
    rows: list[AnalysisRow],
    isotopes: list[tuple[int, int]],
    volume: float,
    output_path: Path,
) -> None:
    rows_sorted = sorted(rows, key=lambda row: float(row["_tdecay_s"]))
    syms = [isotope_symbol(z, a) for z, a in isotopes]

    records: list[AnalysisRow] = []
    for row in rows_sorted:
        record: AnalysisRow = {"CoolingTime": str(row["CoolingTime"])}
        for sym in syms:
            bq = float(row.get(f"{sym} (Bq)", 0.0))
            record[f"{sym} (Bq)"] = bq
            record[f"{sym} (Bq/cm³)"] = bq / volume if volume else 0.0
            record[f"{sym} (% Error)"] = float(row.get(f"{sym} (% Error)", 0.0))
            record[f"{sym} (µg)"] = float(row.get(f"{sym} (µg)", 0.0))
        records.append(record)

    df = pd.DataFrame(records)
    with pd.ExcelWriter(str(output_path), engine="openpyxl") as writer:
        df.to_excel(writer, sheet_name="Activity", index=False)
