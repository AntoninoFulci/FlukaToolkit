from fluka.cli._common import resolve_config


def test_multi_section_file_returns_own_section(tmp_path):
    p = tmp_path / "sim.yaml"
    p.write_text("grid: {template: a.inp}\nanalysis: {units: [21]}\n")
    cfg, mode = resolve_config(p, "analysis")
    assert mode == "section" and cfg == {"units": [21]}


def test_standalone_file_passed_through(tmp_path):
    p = tmp_path / "analysis.yaml"
    p.write_text("units: [21]\nisotopes: {31: 70}\n")
    cfg, mode = resolve_config(p, "analysis")
    assert mode == "standalone" and cfg["units"] == [21]


def test_multi_section_missing_own_section_raises(tmp_path):
    p = tmp_path / "sim.yaml"
    p.write_text("grid: {template: a.inp}\nsubmit: {backend: ts}\n")
    import pytest
    with pytest.raises(KeyError):
        resolve_config(p, "analysis")
