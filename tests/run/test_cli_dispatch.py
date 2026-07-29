import pytest
from fluka.cli._common import resolve, load_sim


def test_common_reexports_resolve_merges_general_into_tool(tmp_path):
    p = tmp_path / "sim.yaml"
    p.write_text("general:\n  backend: ts\nanalysis:\n  units: [21]\n")
    cfg = resolve(p, "analysis")
    assert cfg["backend"] == "ts"    # from general
    assert cfg["units"] == [21]      # from tool section


def test_common_reexports_resolve_tool_overrides_general(tmp_path):
    p = tmp_path / "sim.yaml"
    p.write_text("general:\n  backend: ts\nsubmit:\n  backend: slurm\n")
    cfg = resolve(p, "submit")
    assert cfg["backend"] == "slurm"


def test_common_reexports_load_sim_returns_raw_sections(tmp_path):
    p = tmp_path / "sim.yaml"
    p.write_text("general:\n  backend: ts\nanalysis:\n  units: [21]\n")
    data = load_sim(p)
    assert data["analysis"]["units"] == [21]


def test_common_reexports_load_sim_requires_general(tmp_path):
    p = tmp_path / "sim.yaml"
    p.write_text("analysis: {units: [21]}\n")
    with pytest.raises(Exception):
        load_sim(p)
