import pytest
from unittest.mock import patch, MagicMock
from pathlib import Path
from isotope_analysis.config import AnalysisConfig
from isotope_analysis import analysis as A


def _cfg(directory, **kw):
    return AnalysisConfig(
        directory=directory,
        units=kw.get("units", [21]),
        isotopes=kw.get("isotopes", {27: 60}),
        volume=kw.get("volume", 1000.0),
        executable=kw.get("executable", "usrsuw"),
        output=kw.get("output", "isotopes.xlsx"),
    )


def test_resolve_rnc_uses_existing_rnc(tmp_path):
    (tmp_path / "merged_21.rnc").write_bytes(b"")
    with patch.object(A.subprocess, "run") as mock_run:
        result = A.resolve_rnc(tmp_path, 21, "usrsuw")
    assert result == tmp_path / "merged_21.rnc"
    mock_run.assert_not_called()  # already processed -> no postproc


def test_resolve_rnc_processes_raw_when_no_rnc(tmp_path):
    (tmp_path / "sim001_fort.21").write_bytes(b"")

    def fake_run(*args, **kwargs):
        (tmp_path / "merged_21.rnc").write_bytes(b"")
        return MagicMock(returncode=0, stdout="", stderr="")

    with patch.object(A.subprocess, "run", side_effect=fake_run) as mock_run:
        result = A.resolve_rnc(tmp_path, 21, "usrsuw")
    assert result == tmp_path / "merged_21.rnc"
    mock_run.assert_called_once()


def test_resolve_rnc_returns_none_when_no_data(tmp_path):
    with patch.object(A.subprocess, "run") as mock_run:
        result = A.resolve_rnc(tmp_path, 99, "usrsuw")
    assert result is None
    mock_run.assert_not_called()


def test_run_analysis_writes_workbook(tmp_path):
    (tmp_path / "merged_21.rnc").write_bytes(b"")
    cfg = _cfg(tmp_path, units=[21])
    fake_row = {
        "_tdecay_s": 0.0, "CoolingTime": "0 s", "Parameters": "",
        "Co-60 (Bq)": 1000.0, "Co-60 (% Error)": 5.0, "Co-60 (µg)": 0.42,
    }
    with patch.object(A, "read_resnuclei_file", return_value=fake_row):
        A.run_analysis(cfg)
    assert (tmp_path / "isotopes.xlsx").exists()


def test_run_analysis_no_data_writes_nothing(tmp_path, capsys):
    cfg = _cfg(tmp_path, units=[99])
    A.run_analysis(cfg)
    assert not (tmp_path / "isotopes.xlsx").exists()
    assert "no data" in capsys.readouterr().out.lower()


def test_resolve_rnc_ignores_substring_unit_collision(tmp_path):
    # unit 2 must NOT match merged_21.rnc / merged_22.rnc (substring "2")
    (tmp_path / "merged_21.rnc").write_bytes(b"")
    (tmp_path / "merged_22.rnc").write_bytes(b"")
    with patch.object(A.subprocess, "run") as mock_run:
        result = A.resolve_rnc(tmp_path, 2, "usrsuw")
    assert result is None          # no raw files for unit 2 either
    mock_run.assert_not_called()


def test_resolve_rnc_matches_exact_unit_among_collisions(tmp_path):
    (tmp_path / "merged_2.rnc").write_bytes(b"")
    (tmp_path / "merged_21.rnc").write_bytes(b"")
    with patch.object(A.subprocess, "run") as mock_run:
        result = A.resolve_rnc(tmp_path, 2, "usrsuw")
    assert result == tmp_path / "merged_2.rnc"
    mock_run.assert_not_called()
