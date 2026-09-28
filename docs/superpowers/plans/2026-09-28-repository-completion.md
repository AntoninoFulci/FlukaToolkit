# FlukaToolkit Repository Completion Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Finish repository-hardening follow-up work by documenting existing submission guarantees and bringing `fluka.isotope_inventory` under enforced mypy coverage.

**Architecture:** Keep runtime queue and grid behavior unchanged. Update user-facing wiki text from existing tested behavior, then tighten isotope annotations at data boundaries: `(Z, A)` pairs, heterogeneous analysis rows, and optional binary blocks. Enable mypy only after runtime tests and explicit binary-failure handling are in place.

**Tech Stack:** Python 3.10+, pytest, mypy, Ruff, pandas/openpyxl, setuptools/build.

**Spec:** `docs/superpowers/specs/2026-09-28-repository-completion-design.md`

## Global Constraints

- Preserve all six console commands and current `sim.yaml` schema.
- Change no production code under `src/fluka/queue` or `src/fluka/grid`.
- Implement none of the deferred grid, scheduler, cancellation, or empty-result policies.
- Keep Python compatibility at 3.10 or newer.
- Add no runtime dependency.
- Add no `type: ignore`, broad `Any` escape, or replacement mypy exclusion.
- Preserve isotope values, workbook columns, parsing semantics, and CLI output.
- Add no license file or package license metadata.
- Do not push or create a pull request during implementation.

## Review Focus

- A detector with a missing required data block must raise explicit `OSError`; Task 2 adds `test_read_resnuclei_file_missing_detector_data_raises`.
- A statistics record with no uncertainty payload must produce zero uncertainty, not crash; Task 2 adds `test_read_resnuclei_file_missing_stat_data_uses_zero_error`.
- An evolution detector missing its decay-time block must raise explicit `OSError`; Task 3 adds `test_missing_evolution_decay_time_raises`.
- Duplicate or pre-existing collection destinations must remain rejected without source deletion; Task 1 reruns existing collision and preservation tests.
- One failed scheduler submission must not hide later attempts or successful results; Task 1 reruns existing submission aggregation tests.

---

### Task 1: Document Current Submission and Collection Guarantees

**Files:**
- Modify: `wiki/fluka-submit.md:98-135`
- Test: `tests/queue/test_service.py`
- Test: `tests/queue/test_collect_results.py`

**Interfaces:**
- Consumes: existing `SubmissionBatchError`, collision-aware `MovePlan`, and collection rollback behavior.
- Produces: user-facing guarantees for partial submission failures, collision rejection, and job-directory retention.

- [ ] **Step 1: Confirm behavior tests are green before changing documentation**

Run:

```bash
python3 -m pytest \
  tests/queue/test_service.py \
  tests/queue/test_collect_results.py \
  -q
```

Expected: all tests pass, including `test_submit_prepared_attempts_all_jobs_then_raises`, `test_duplicate_destination_aborts_parent_without_moving`, `test_existing_destination_is_never_overwritten`, and `test_execute_move_failure_preserves_all_sibling_job_dirs`.

- [ ] **Step 2: Add submission-failure contract**

Insert after `## What it produces` and its tree example:

```markdown
## Submission failures

Submission attempts every independently prepared job even when one scheduler call
fails. Each failed job is reported with its iteration and scheduler error; successful
submissions remain successful. After all jobs have been attempted, any failure makes
the command exit non-zero.
```

- [ ] **Step 3: Replace collection paragraph with collision and retention contract**

Replace current text under `## Collecting results` with:

```markdown
Once jobs finish, `fluka-run analyze` (or `fluka.queue.collect_results`
directly) gathers each job's `.root` files into a `root_files/` directory
per parent run, printing a table of the planned moves and asking for
confirmation.

Collection scans destinations before moving anything. Duplicate filenames from
different jobs, or files already present under `root_files/`, are reported as
collisions and reject collection for the affected parent run. Existing destinations
are never overwritten.

Source `job_*` directories are removed only after every file for that parent has been
collected successfully. Planning or execution failure preserves all source job
directories; destinations created during a failed execution are rolled back when
they can be identified safely. Jobs with no `.root` file are flagged.
```

- [ ] **Step 4: Verify wording covers every required guarantee**

Run:

```bash
rg -n "attempts every|exit non-zero|collisions|never overwritten|preserves all source" \
  wiki/fluka-submit.md
git diff --check
```

Expected: five matching guarantee lines; no whitespace errors.

- [ ] **Step 5: Commit documentation**

```bash
git add wiki/fluka-submit.md
git commit -m "docs: describe submission failure guarantees"
```

### Task 2: Unify Isotope and Analysis-Row Types

**Files:**
- Modify: `tests/isotope_inventory/test_reader.py`
- Modify: `src/fluka/isotope_inventory/reader.py:1-65`
- Modify: `src/fluka/isotope_inventory/analysis.py:7-71`
- Modify: `src/fluka/isotope_inventory/excel.py:1-32`

**Interfaces:**
- Consumes: `AnalysisConfig.isotopes: list[tuple[int, int]]`, `Resnuclei.read_data()`, and `Resnuclei.read_stat()`.
- Produces: `AnalysisValue = str | float`, `AnalysisRow = dict[str, AnalysisValue]`, `read_resnuclei_file(path: Path, requested_isotopes: list[tuple[int, int]], params: dict[str, object]) -> AnalysisRow | None`, and `write_activity_workbook(rows: list[AnalysisRow], isotopes: list[tuple[int, int]], volume: float, output_path: Path) -> None`.

- [ ] **Step 1: Add failing missing-detector-data test**

Append to `tests/isotope_inventory/test_reader.py`:

```python
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
```

- [ ] **Step 2: Add failing missing-statistics-payload test**

Append:

```python
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
```

- [ ] **Step 3: Run both tests and verify failures**

Run:

```bash
python3 -m pytest \
  tests/isotope_inventory/test_reader.py::test_read_resnuclei_file_missing_detector_data_raises \
  tests/isotope_inventory/test_reader.py::test_read_resnuclei_file_missing_stat_data_uses_zero_error \
  -q
```

Expected: first test fails because `None` reaches `unpack_array`; second fails with a `TypeError` from `struct.unpack`.

- [ ] **Step 4: Define typed analysis-row boundary and explicit optional-block handling**

Update `src/fluka/isotope_inventory/reader.py`:

```python
AnalysisValue = str | float
AnalysisRow = dict[str, AnalysisValue]


def read_resnuclei_file(
    path: Path,
    requested_isotopes: list[tuple[int, int]],
    params: dict[str, object],
) -> AnalysisRow | None:
```

Replace data/stat decoding with:

```python
    data = resn.read_data(0)
    if data is None:
        raise OSError(f"{path}: missing detector data block")
    stat = resn.read_stat(0)
    fdata = unpack_array(data)
    stat_data = stat[5] if stat is not None else None
    edata = unpack_array(stat_data) if stat_data is not None else None
```

Type row explicitly:

```python
    row: AnalysisRow = {
        "_tdecay_s": tdecay_s,
        "CoolingTime": format_decay_time(tdecay_s),
        "Parameters": " ".join(f"{k}={v}" for k, v in params.items()),
    }
```

- [ ] **Step 5: Propagate exact types through analysis and workbook generation**

In `src/fluka/isotope_inventory/analysis.py`, import `AnalysisRow` and change the collection:

```python
from .reader import AnalysisRow, read_resnuclei_file


def run_analysis(config: AnalysisConfig) -> None:
    directory = config.directory
    rows: list[AnalysisRow] = []
```

In `src/fluka/isotope_inventory/excel.py`, import `AnalysisRow` and use:

```python
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
```

Keep existing DataFrame and Excel writer statements unchanged after this block.

- [ ] **Step 6: Run isotope behavior tests**

Run:

```bash
python3 -m pytest tests/isotope_inventory/test_reader.py tests/isotope_inventory/test_excel.py tests/isotope_inventory/test_analysis.py -q
```

Expected: all tests pass; workbook values and columns remain unchanged.

- [ ] **Step 7: Commit typed isotope data flow**

```bash
git add \
  tests/isotope_inventory/test_reader.py \
  src/fluka/isotope_inventory/reader.py \
  src/fluka/isotope_inventory/analysis.py \
  src/fluka/isotope_inventory/excel.py
git commit -m "refactor(isotopes): type analysis data flow"
```

### Task 3: Type Binary RESNUCLEi State and Enforce Mypy Coverage

**Files:**
- Modify: `tests/isotope_inventory/test_resnuclei.py`
- Modify: `src/fluka/isotope_inventory/resnuclei.py:1-192`
- Modify: `pyproject.toml:62-72`

**Interfaces:**
- Consumes: Python binary streams and existing Fortran record layout.
- Produces: `fortran_read(f: BinaryIO) -> bytes | None`, `fortran_skip(f: BinaryIO) -> int`, `unpack_array(data: bytes) -> tuple[float, ...]`, `StatisticBlocks`, checked `Resnuclei._file`, and repository-wide mypy coverage for `fluka.isotope_inventory`.

- [ ] **Step 1: Add failing truncated-evolution test**

Append to `tests/isotope_inventory/test_resnuclei.py` and import `Resnuclei`:

```python
from fluka.isotope_inventory.resnuclei import Resnuclei, fortran_read, fortran_skip, unpack_array


def test_missing_evolution_decay_time_raises(tmp_path):
    base = struct.pack("=80s32sfi", b"title", b"time", 1.0, -1)
    evolution = struct.pack("=i", 0)
    detector = struct.pack("=i10siif3i", 1, b"detector", 0, 0, 1.0, 1, 1, 0)
    path = tmp_path / "truncated.rnc"
    path.write_bytes(make_block(base) + make_block(evolution) + make_block(detector))

    with pytest.raises(OSError, match="decay time"):
        Resnuclei(str(path))
```

- [ ] **Step 2: Run test and verify failure**

Run:

```bash
python3 -m pytest \
  tests/isotope_inventory/test_resnuclei.py::test_missing_evolution_decay_time_raises \
  -q
```

Expected: FAIL with `TypeError: a bytes-like object is required, not 'NoneType'`.

- [ ] **Step 3: Capture current mypy failures**

Run:

```bash
python3 -m mypy src/fluka/isotope_inventory
```

Expected: failures remain in `resnuclei.py` for optional `_f`, missing decay data, and untyped tuple returns. Errors previously caused by isotope container mismatches are gone after Task 2.

- [ ] **Step 4: Add binary stream and statistics types**

Update imports and module-level signatures in `src/fluka/isotope_inventory/resnuclei.py`:

```python
from typing import BinaryIO, TypeAlias


StatisticBlocks: TypeAlias = tuple[
    bytes | None,
    bytes | None,
    bytes | None,
    bytes | None,
    bytes | None,
    bytes | None,
    bytes | None,
]


def fortran_read(f: BinaryIO) -> bytes | None:
    blen = f.read(4)
    if not blen:
        return None
    (size,) = struct.unpack("=i", blen)
    data = f.read(size)
    blen2 = f.read(4)
    if blen != blen2:
        raise OSError("Reading Fortran block")
    return data


def fortran_skip(f: BinaryIO) -> int:
    blen = f.read(4)
    if not blen:
        return 0
    (size,) = struct.unpack("=i", blen)
    f.seek(size, 1)
    blen2 = f.read(4)
    if blen != blen2:
        raise OSError("Skipping Fortran block")
    return size


def unpack_array(data: bytes) -> tuple[float, ...]:
    return struct.unpack(f"={len(data) // 4}f", data)
```

These annotations leave record-reading behavior unchanged.

- [ ] **Step 5: Guard open-file state centrally**

In `Resnuclei.__init__`, annotate state:

```python
        self._f: BinaryIO | None = None
```

Add after `_close()`:

```python
    @property
    def _file(self) -> BinaryIO:
        if self._f is None:
            raise RuntimeError("RESNUCLEi file is not open")
        return self._f
```

Replace each stream argument or stream operation from `self._f` to checked `self._file`, including:

```python
data = fortran_read(self._file)
fortran_skip(self._file)
self._file.seek(self.statpos)
self.statpos = self._file.tell()
```

Keep `_open()` and `_close()` ownership unchanged so every public read path still closes the file in `finally`.

- [ ] **Step 6: Guard missing evolution decay block and type statistics return**

Replace evolution decay decoding with:

```python
                if self.evol:
                    data = fortran_read(self._file)
                    if data is None:
                        raise OSError("Unexpected EOF reading decay time")
                    self.tdecay = struct.unpack("=f", data)[0]
```

Change signature:

```python
    def read_stat(self, n: int) -> StatisticBlocks | None:
```

Keep returned seven-element tuple order unchanged: total, A, errA, Z, errZ, data, iso.

- [ ] **Step 7: Enable isotope package in configured mypy run**

Replace mypy file list and remove skip override in `pyproject.toml`:

```toml
[tool.mypy]
python_version = "3.10"
files = [
    "src/fluka/queue",
    "src/fluka/run",
    "src/fluka/cli",
    "src/fluka/isotope_inventory",
]
ignore_missing_imports = true
no_site_packages = true
check_untyped_defs = true
no_implicit_optional = true
```

- [ ] **Step 8: Run focused tests and mypy**

Run:

```bash
python3 -m pytest tests/isotope_inventory -q
python3 -m mypy src/fluka/isotope_inventory
python3 -m mypy
```

Expected: isotope tests pass; both mypy commands report `Success: no issues found`.

- [ ] **Step 9: Commit binary typing and enforcement**

```bash
git add \
  tests/isotope_inventory/test_resnuclei.py \
  src/fluka/isotope_inventory/resnuclei.py \
  pyproject.toml
git commit -m "chore(types): check isotope inventory"
```

### Task 4: Run Release-Readiness Gates

**Files:**
- Verify only: entire repository

**Interfaces:**
- Consumes: completed documentation and typing commits.
- Produces: evidence that lint, format, types, tests, coverage, package build, and repository state are release-ready.

- [ ] **Step 1: Run lint and formatting checks**

Run:

```bash
python3 -m ruff check src tests
python3 -m ruff format --check src tests
```

Expected: both commands exit 0 without modifying files.

- [ ] **Step 2: Run configured type check**

Run:

```bash
python3 -m mypy
```

Expected: `Success: no issues found` and isotope modules appear in checked file count.

- [ ] **Step 3: Run full coverage-enabled suite**

Run:

```bash
python3 -m pytest --cov=fluka --cov-report=term-missing
```

Expected: all tests pass; coverage report is emitted. No percentage threshold applies.

- [ ] **Step 4: Build distributions and run wheel asset smoke test**

Run:

```bash
python3 -m build
python3 -m pytest tests/test_wheel_package.py -q
```

Expected: source archive and wheel build successfully; packaged compiler-asset test passes.

- [ ] **Step 5: Verify final diff and publication boundary**

Run:

```bash
git diff --check
git status --short --branch
git log --oneline origin/main..main
git rev-list --left-right --count origin/main...main
```

Expected: working tree clean; local `main` is zero commits behind and includes completion commits ahead of `origin/main`. Stop before push, branch creation, or pull request.

## Self-Review Record

- Spec coverage: wiki guarantees are Task 1; isotope container and row types are Task 2; binary typing and mypy enforcement are Task 3; release verification and publication boundary are Task 4; deferred policies remain recorded only in the spec.
- Type consistency: `AnalysisConfig.isotopes`, reader, analysis, and workbook all use `list[tuple[int, int]]`; `AnalysisRow` originates in `reader.py` and is consumed unchanged by analysis and Excel generation; `StatisticBlocks[5]` remains uncertainty data.
- Review focus: each listed failure mode has a new or existing named test executed by its owning task.
- Scope: no queue/grid runtime edits, new dependencies, license changes, or publication actions.
