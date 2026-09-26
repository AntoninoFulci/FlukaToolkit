from pathlib import Path

from fluka.queue.check_seeds import has_duplicates, main, scan_seeds


def _make_job(root: Path, parent: str, job: str, seed_line: str):
    d = root / parent / job
    d.mkdir(parents=True)
    (d / f"{job}.inp").write_text(seed_line)


def test_scan_seeds_groups_by_seed(tmp_path):
    _make_job(tmp_path, "sim", "job_0001", "RANDOMIZ          1.  111\n")
    _make_job(tmp_path, "sim", "job_0002", "RANDOMIZ          1.  222\n")
    _make_job(tmp_path, "sim", "job_0003", "RANDOMIZ          1.  111\n")
    result = scan_seeds(Path(tmp_path))
    assert set(result.keys()) == {111, 222}
    assert len(result[111]) == 2
    assert len(result[222]) == 1


def test_has_duplicates_true_when_seed_shared():
    seeds = {111: [Path("a"), Path("b")], 222: [Path("c")]}
    assert has_duplicates(seeds) is True


def test_has_duplicates_false_when_all_unique():
    seeds = {111: [Path("a")], 222: [Path("b")]}
    assert has_duplicates(seeds) is False


def test_main_returns_1_on_duplicate(tmp_path, monkeypatch):
    _make_job(tmp_path, "sim", "job_0001", "RANDOMIZ          1.  111\n")
    _make_job(tmp_path, "sim", "job_0002", "RANDOMIZ          1.  111\n")
    monkeypatch.chdir(tmp_path)
    assert main() == 1


def test_main_returns_0_when_all_unique(tmp_path, monkeypatch):
    _make_job(tmp_path, "sim", "job_0001", "RANDOMIZ          1.  111\n")
    _make_job(tmp_path, "sim", "job_0002", "RANDOMIZ          1.  222\n")
    monkeypatch.chdir(tmp_path)
    assert main() == 0
