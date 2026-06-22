import pytest
import pandas as pd
from isotope_analysis.excel import write_activity_workbook


def test_write_activity_workbook(tmp_path):
    rows = [
        {
            "_tdecay_s": 86400.0, "CoolingTime": "1.0 d", "Parameters": "",
            "Co-60 (Bq)": 1000.0, "Co-60 (% Error)": 5.0, "Co-60 (µg)": 0.42,
        },
        {
            "_tdecay_s": 0.0, "CoolingTime": "0 s", "Parameters": "",
            "Co-60 (Bq)": 2000.0, "Co-60 (% Error)": 4.0, "Co-60 (µg)": 0.84,
        },
    ]
    out = tmp_path / "out.xlsx"
    write_activity_workbook(rows, isotopes={27: 60}, volume=1000.0, output_path=out)

    assert out.exists()
    df = pd.read_excel(out, sheet_name="Activity")
    # sorted by _tdecay_s ascending => first row is "0 s"
    assert df["CoolingTime"].iloc[0] == "0 s"
    assert df["Co-60 (Bq)"].iloc[0] == pytest.approx(2000.0)
    assert df["Co-60 (Bq/cm³)"].iloc[0] == pytest.approx(2.0)
    assert "Co-60 (% Error)" in df.columns
    assert "Co-60 (µg)" in df.columns
    # internal sort key must not leak into the sheet
    assert "_tdecay_s" not in df.columns
