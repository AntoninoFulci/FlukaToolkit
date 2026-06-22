import pytest
from pathlib import Path
from isotope_analysis.config import load_analysis_config, AnalysisConfig


def _write_config(tmp_path, body: str) -> Path:
    p = tmp_path / "analysis.yaml"
    p.write_text(body)
    return p


def test_load_full_config(tmp_path):
    sim = tmp_path / "sim"
    sim.mkdir()
    cfg = _write_config(tmp_path, f"""
analysis:
  directory: {sim}
  units: [21, 22]
  executable: usrsuw
  volume: 1000
  isotopes:
    31: 70
    30: 69
  output: out.xlsx
""")
    c = load_analysis_config(cfg)
    assert isinstance(c, AnalysisConfig)
    assert c.directory == sim
    assert c.units == [21, 22]
    assert c.executable == "usrsuw"
    assert c.volume == 1000.0
    assert c.isotopes == {31: 70, 30: 69}
    assert c.output == "out.xlsx"


def test_defaults_applied(tmp_path):
    sim = tmp_path / "sim"
    sim.mkdir()
    cfg = _write_config(tmp_path, f"""
analysis:
  directory: {sim}
  units: [21]
  volume: 500
  isotopes:
    27: 60
""")
    c = load_analysis_config(cfg)
    assert c.executable == "usrsuw"
    assert c.output == "isotopes.xlsx"


def test_missing_directory_field_raises(tmp_path):
    cfg = _write_config(tmp_path, """
analysis:
  units: [21]
  volume: 1
  isotopes:
    27: 60
""")
    with pytest.raises(ValueError, match="directory"):
        load_analysis_config(cfg)


def test_nonexistent_directory_raises(tmp_path):
    cfg = _write_config(tmp_path, f"""
analysis:
  directory: {tmp_path / 'does_not_exist'}
  units: [21]
  volume: 1
  isotopes:
    27: 60
""")
    with pytest.raises(ValueError, match="does not exist"):
        load_analysis_config(cfg)


def test_empty_units_raises(tmp_path):
    sim = tmp_path / "sim"
    sim.mkdir()
    cfg = _write_config(tmp_path, f"""
analysis:
  directory: {sim}
  units: []
  volume: 1
  isotopes:
    27: 60
""")
    with pytest.raises(ValueError, match="units"):
        load_analysis_config(cfg)
