import struct
from unittest.mock import MagicMock, patch

import pytest

from fluka.isotope_inventory.reader import read_resnuclei_file
from fluka.isotope_inventory.resnuclei import Detector


def make_float_bytes(*values):
    return struct.pack(f"={len(values)}f", *values)


def test_missing_rnc_file_is_skipped(tmp_path):
    row = read_resnuclei_file(
        path=tmp_path / "nonexistent",
        requested_isotopes=[(27, 60)],
        params={},
    )
    assert row is None


def test_read_resnuclei_file_returns_known_isotope(tmp_path):
    det = Detector(num=1, name="test", volume=2.0, mhigh=2, zhigh=2, nmzmin=0)
    fdata_bytes = make_float_bytes(100.0, 50.0, 30.0, 20.0)
    edata_bytes = make_float_bytes(0.05, 0.10, 0.15, 0.20)

    mock_resn = MagicMock()
    mock_resn.detector = [det]
    mock_resn.tdecay = 86400.0
    mock_resn.read_data.return_value = fdata_bytes
    mock_resn.read_stat.return_value = (None, None, None, None, None, edata_bytes, None)

    rnc_path = tmp_path / "merged_21.rnc"
    rnc_path.write_bytes(b"")

    with patch("fluka.isotope_inventory.reader.Resnuclei", return_value=mock_resn):
        row = read_resnuclei_file(
            path=rnc_path,
            requested_isotopes=[(1, 3)],
            params={"beame": 0.05},
        )

    assert row is not None
    assert row["H-3 (Bq)"] == pytest.approx(200.0)
    assert row["H-3 (% Error)"] == pytest.approx(5.0)
    assert "d" in row["CoolingTime"]
    assert "beame=0.05" in row["Parameters"]


def test_read_resnuclei_file_isotope_not_present_gives_zero(tmp_path):
    det = Detector(num=1, name="test", volume=1.0, mhigh=2, zhigh=2, nmzmin=0)
    fdata_bytes = make_float_bytes(0.0, 0.0, 0.0, 0.0)
    edata_bytes = make_float_bytes(0.0, 0.0, 0.0, 0.0)

    mock_resn = MagicMock()
    mock_resn.detector = [det]
    mock_resn.tdecay = 0.0
    mock_resn.read_data.return_value = fdata_bytes
    mock_resn.read_stat.return_value = (None, None, None, None, None, edata_bytes, None)

    rnc_path = tmp_path / "merged_21.rnc"
    rnc_path.write_bytes(b"")

    with patch("fluka.isotope_inventory.reader.Resnuclei", return_value=mock_resn):
        row = read_resnuclei_file(
            path=rnc_path,
            requested_isotopes=[(27, 60)],
            params={},
        )

    assert row is not None
    assert row["Co-60 (Bq)"] == pytest.approx(0.0)
    assert row["Co-60 (% Error)"] == pytest.approx(0.0)


def test_read_resnuclei_file_missing_detector_data_raises(tmp_path):
    mock_resn = MagicMock()
    mock_resn.detector = [Detector(num=1, name="test", volume=1.0, mhigh=1, zhigh=1)]
    mock_resn.read_data.return_value = None
    mock_resn.read_stat.return_value = None
    rnc_path = tmp_path / "merged_21.rnc"
    rnc_path.write_bytes(b"")

    with patch("fluka.isotope_inventory.reader.Resnuclei", return_value=mock_resn):
        with pytest.raises(OSError, match="missing detector data"):
            read_resnuclei_file(rnc_path, [(1, 1)], {})


def test_read_resnuclei_file_missing_stat_data_uses_zero_error(tmp_path):
    det = Detector(num=1, name="test", volume=1.0, mhigh=2, zhigh=2, nmzmin=0)
    mock_resn = MagicMock()
    mock_resn.detector = [det]
    mock_resn.tdecay = 0.0
    mock_resn.read_data.return_value = make_float_bytes(100.0, 0.0, 0.0, 0.0)
    mock_resn.read_stat.return_value = (None, None, None, None, None, None, None)
    rnc_path = tmp_path / "merged_21.rnc"
    rnc_path.write_bytes(b"")

    with patch("fluka.isotope_inventory.reader.Resnuclei", return_value=mock_resn):
        row = read_resnuclei_file(rnc_path, [(1, 3)], {})

    assert row is not None
    assert row["H-3 (% Error)"] == pytest.approx(0.0)
