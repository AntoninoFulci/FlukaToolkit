import os
import pytest
from pathlib import Path
from unittest.mock import patch
from core.fluka import generate_input, detect_fluka_path, parse_randomiz, allocate_seed, scan_existing_seeds


def test_generate_input_renames_file(tmp_path):
    base = "simulation"
    inp = tmp_path / f"{base}.inp"
    inp.write_text("TITLE test\nRANDOMIZ          1.  12345678\nSTOP\n")

    result = generate_input(base, 1, str(tmp_path))

    assert result == f"{base}_0001.inp"
    assert not (tmp_path / f"{base}.inp").exists()
    assert (tmp_path / result).exists()


def test_generate_input_updates_randomiz_seed(tmp_path):
    base = "simulation"
    inp = tmp_path / f"{base}.inp"
    inp.write_text("RANDOMIZ          1.  12345678\n")

    generate_input(base, 1, str(tmp_path))

    content = (tmp_path / f"{base}_0001.inp").read_text()
    assert "RANDOMIZ" in content
    assert "12345678" not in content


def test_generate_input_zero_pads_iteration(tmp_path):
    base = "sim"
    (tmp_path / f"{base}.inp").write_text("RANDOMIZ          1.  99999999\n")
    result = generate_input(base, 42, str(tmp_path))
    assert result == "sim_0042.inp"


def test_detect_fluka_path_returns_paths():
    with patch("subprocess.check_output", side_effect=[b"/usr/local/bin\n", b"/usr/local/fluka\n"]):
        bin_path, folder_path = detect_fluka_path()
    assert bin_path == "/usr/local/bin"
    assert folder_path == "/usr/local/fluka"


def test_detect_fluka_path_exits_if_not_found():
    import subprocess
    with patch("subprocess.check_output", side_effect=subprocess.CalledProcessError(1, "fluka-config")):
        with pytest.raises(SystemExit):
            detect_fluka_path()


def test_generate_input_raises_if_no_randomiz(tmp_path):
    base = "sim"
    (tmp_path / f"{base}.inp").write_text("TITLE test\nSTOP\n")
    with pytest.raises(ValueError, match="RANDOMIZ"):
        generate_input(base, 1, str(tmp_path))


def test_generate_input_replaces_start_card(tmp_path):
    base = "sim"
    (tmp_path / f"{base}.inp").write_text("RANDOMIZ          1.  12345678\nSTART         1000.0\nSTOP\n")
    generate_input(base, 1, str(tmp_path), nprim=5000)
    content = (tmp_path / f"{base}_0001.inp").read_text()
    assert "START         5000.0\n" in content


def test_generate_input_start_columnar_format(tmp_path):
    base = "sim"
    (tmp_path / f"{base}.inp").write_text("RANDOMIZ          1.  12345678\nSTART         1000.0\n")
    generate_input(base, 1, str(tmp_path), nprim=1000)
    line = next(l for l in (tmp_path / f"{base}_0001.inp").read_text().splitlines() if l.startswith("START"))
    assert line[0:8] == "START   "
    assert len(line) == 20


def test_generate_input_raises_if_no_start_when_nprim_set(tmp_path):
    base = "sim"
    (tmp_path / f"{base}.inp").write_text("RANDOMIZ          1.  12345678\nSTOP\n")
    with pytest.raises(ValueError, match="START"):
        generate_input(base, 1, str(tmp_path), nprim=1000)


def test_generate_input_nprim_none_leaves_start_unchanged(tmp_path):
    base = "sim"
    original_start = "START         1000.0\n"
    (tmp_path / f"{base}.inp").write_text(f"RANDOMIZ          1.  12345678\n{original_start}")
    generate_input(base, 1, str(tmp_path), nprim=None)
    content = (tmp_path / f"{base}_0001.inp").read_text()
    assert original_start in content


def test_detect_fluka_path_exits_if_command_missing():
    with patch("subprocess.check_output", side_effect=FileNotFoundError):
        with pytest.raises(SystemExit):
            detect_fluka_path()


def test_parse_randomiz_fixed_format(tmp_path):
    inp = tmp_path / "a.inp"
    inp.write_text("TITLE test\nRANDOMIZ          1.  12345678\nSTOP\n")
    assert parse_randomiz(Path(inp)) == 12345678


def test_parse_randomiz_free_format(tmp_path):
    inp = tmp_path / "b.inp"
    inp.write_text("RANDOMIZ 1.0 7777\n")
    assert parse_randomiz(Path(inp)) == 7777


def test_parse_randomiz_missing_card_returns_none(tmp_path):
    inp = tmp_path / "c.inp"
    inp.write_text("TITLE test\nSTOP\n")
    assert parse_randomiz(Path(inp)) is None


def test_parse_randomiz_no_seed_value_returns_none(tmp_path):
    inp = tmp_path / "d.inp"
    inp.write_text("RANDOMIZ          1.\n")
    assert parse_randomiz(Path(inp)) is None


def test_allocate_seed_returns_unused_and_records_it():
    used = set()
    s = allocate_seed(used)
    assert s in used
    assert 1 <= s <= int(9e7)


def test_allocate_seed_redraws_on_collision():
    used = {111}
    with patch("core.fluka.random.randint", side_effect=[111, 222]):
        s = allocate_seed(used)
    assert s == 222
    assert used == {111, 222}


def test_scan_existing_seeds_collects_from_job_dirs(tmp_path):
    out = tmp_path / "sim"
    out.mkdir()
    j1 = out / "job_0001"
    j1.mkdir()
    (j1 / "sim_0001.inp").write_text("RANDOMIZ          1.  111\n")
    j2 = out / "job_0002"
    j2.mkdir()
    (j2 / "sim_0002.inp").write_text("RANDOMIZ          1.  222\n")
    assert scan_existing_seeds(Path(out)) == {111, 222}


def test_scan_existing_seeds_empty_dir_returns_empty_set(tmp_path):
    out = tmp_path / "sim"
    out.mkdir()
    assert scan_existing_seeds(Path(out)) == set()


def test_generate_input_uses_supplied_seed(tmp_path):
    base = "sim"
    (tmp_path / f"{base}.inp").write_text("RANDOMIZ          1.  12345678\n")
    generate_input(base, 1, str(tmp_path), seed=4242)
    content = (tmp_path / f"{base}_0001.inp").read_text()
    assert "4242" in content
    assert "12345678" not in content


from core.fluka import find_duplicate_seeds


def test_find_duplicate_seeds_returns_only_shared(tmp_path):
    out = tmp_path / "sim"
    for name, seed in [("job_0001", 111), ("job_0002", 222), ("job_0003", 111)]:
        d = out / name
        d.mkdir(parents=True)
        (d / f"{name}.inp").write_text(f"RANDOMIZ          1.  {seed}\n")
    dupes = find_duplicate_seeds(Path(out))
    assert set(dupes.keys()) == {111}
    assert len(dupes[111]) == 2


def test_find_duplicate_seeds_empty_when_all_unique(tmp_path):
    out = tmp_path / "sim"
    for name, seed in [("job_0001", 1), ("job_0002", 2)]:
        d = out / name
        d.mkdir(parents=True)
        (d / f"{name}.inp").write_text(f"RANDOMIZ          1.  {seed}\n")
    assert find_duplicate_seeds(Path(out)) == {}
