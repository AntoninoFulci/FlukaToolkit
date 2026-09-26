# FlukaToolkit Repository Hardening Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Remove repository debris, fix data-loss and false-success paths, consolidate submission infrastructure, and add enforceable quality gates without changing console commands or `sim.yaml`.

**Architecture:** Keep scheduler-specific backend classes, but give them one registry and one typed submission configuration. Move job execution into a service that raises domain errors; leave parsing, messages, confirmation, and exit codes at CLI boundaries. Apply correctness fixes before structural refactors so every stage remains testable.

**Tech Stack:** Python 3.10+, setuptools, pytest, Ruff, mypy, pytest-cov, GitHub Actions.

**Spec:** `docs/superpowers/specs/2026-09-26-repository-hardening-design.md`

## Global Constraints

- Preserve console commands `fluka-grid`, `fluka-submit`, `fluka-analysis`, `fluka-compile`, `fluka-run`, and `fluka-status`.
- Preserve existing `sim.yaml` keys and merge behavior.
- Internal Python APIs may change without compatibility shims.
- Add no runtime configuration dependency and no backend plugin framework.
- Add no license file or package license metadata.
- Never overwrite simulation output or delete job directories after collection failure.
- Every behavioral change follows red-green-refactor; full `pytest` must remain green after each task.

## Review Focus

- Two job directories producing the same ROOT filename must fail before any move; Task 2 adds this test.
- A pre-existing destination file must remain unchanged and preserve every job directory; Task 2 adds this test.
- One scheduler submission failure among successful jobs must yield an overall non-zero result without skipping later jobs; Task 6 adds this test.
- A disappeared scheduler command must fall back to the correct sentinel and distinguish success from failure; Task 4 adds this test.
- Direct CLI, legacy YAML, and merged `sim.yaml` must create equivalent typed values for shared fields; Task 5 adds this test.

---

### Task 1: Remove Generated Repository Debris

**Files:**
- Modify: `.gitignore`
- Delete locally: `.DS_Store`, `src/.DS_Store`, `.pytest_cache/`, `build/`, `src/flukatoolkit.egg-info/`, every `__pycache__/`, every `*.pyc`
- Preserve locally: `graphify-out/`, `docs/legacy/`, `.superpowers/`

**Interfaces:**
- Consumes: current ignore policy.
- Produces: clean working tree where Graphify and future coverage artifacts stay untracked.

- [ ] **Step 1: Capture cleanup targets without deleting them**

Run:

```bash
find . -type d -name __pycache__ -prune -print
find . -type f -name '*.pyc' -print
du -sh .pytest_cache build src/flukatoolkit.egg-info graphify-out 2>/dev/null
```

Expected: only generated caches/build outputs plus retained `graphify-out/` are listed.

- [ ] **Step 2: Extend ignore policy**

Add:

```gitignore
.coverage
htmlcov/
graphify-out/
```

Keep `docs/`, `.superpowers/`, and current simulation-output rules unchanged.

- [ ] **Step 3: Remove only verified generated targets**

Run exact paths plus targeted cache searches:

```bash
rm -rf .pytest_cache build src/flukatoolkit.egg-info
rm -f .DS_Store src/.DS_Store
find src tests -type d -name __pycache__ -prune -exec rm -rf {} +
find src tests -type f -name '*.pyc' -delete
```

Expected: targets disappear; `graphify-out/` and ignored local documentation remain.

- [ ] **Step 4: Verify clean baseline**

Run:

```bash
git status --short --ignored
python3 -m pytest -q
```

Expected: 335 tests pass before later test additions; `graphify-out/` appears ignored, not untracked.

- [ ] **Step 5: Commit**

```bash
git add .gitignore
git commit -m "chore: ignore generated analysis artifacts"
```

### Task 2: Make ROOT Collection Collision-Safe

**Files:**
- Modify: `src/fluka/queue/collect_results.py`
- Modify: `tests/queue/test_collect_results.py`

**Interfaces:**
- Consumes: `scan_all(cwd: Path) -> MovePlan`, `execute_plan(plan: MovePlan) -> int`.
- Produces: `CollectionCollision`, `MovePlan.collisions`, collision-aware planning and execution.

- [ ] **Step 1: Write failing duplicate-source test**

Add:

```python
def test_duplicate_destination_aborts_parent_without_moving(tmp_path):
    make_tree(tmp_path, {
        "SimLead": {
            "job_0001": ["dump.root"],
            "job_0002": ["dump.root"],
        }
    })
    plan = scan_all(tmp_path)

    assert [c.dest.name for c in plan.collisions] == ["dump.root"]
    assert execute_plan(plan) == 1
    assert (tmp_path / "SimLead" / "job_0001" / "dump.root").exists()
    assert (tmp_path / "SimLead" / "job_0002" / "dump.root").exists()
    assert not (tmp_path / "SimLead" / "root_files" / "dump.root").exists()
```

- [ ] **Step 2: Verify duplicate test is red**

Run: `python3 -m pytest tests/queue/test_collect_results.py::test_duplicate_destination_aborts_parent_without_moving -q`

Expected: FAIL because `MovePlan` has no `collisions`.

- [ ] **Step 3: Write failing existing-destination test**

Add:

```python
def test_existing_destination_is_never_overwritten(tmp_path):
    make_tree(tmp_path, {"SimLead": {"job_0001": ["dump.root"]}})
    dest_dir = tmp_path / "SimLead" / "root_files"
    dest_dir.mkdir()
    dest = dest_dir / "dump.root"
    dest.write_bytes(b"original")

    plan = scan_all(tmp_path)

    assert execute_plan(plan) == 1
    assert dest.read_bytes() == b"original"
    assert (tmp_path / "SimLead" / "job_0001" / "dump.root").exists()
```

- [ ] **Step 4: Verify existing-destination test is red**

Run: `python3 -m pytest tests/queue/test_collect_results.py::test_existing_destination_is_never_overwritten -q`

Expected: FAIL because current scan skips the parent and returns success.

- [ ] **Step 5: Implement collision model and parent-level abort**

Add:

```python
@dataclass
class CollectionCollision:
    parent_dir: Path
    dest: Path
    sources: list[Path]
    destination_exists: bool = False

@dataclass
class MovePlan:
    moves: list[FileMove] = field(default_factory=list)
    empty_jobs: list[EmptyJob] = field(default_factory=list)
    collisions: list[CollectionCollision] = field(default_factory=list)
```

During scan, group candidate moves by destination. Create a collision when a group has more than one source or when `dest.exists()`; set `destination_exists` for the latter. Retain moves only for parents without collisions. `display_plan()` prints every collision. `execute_plan()` returns `1` when collisions exist and performs no moves for those parents.

- [ ] **Step 6: Run collection tests**

Run: `python3 -m pytest tests/queue/test_collect_results.py -q`

Expected: all collection tests pass after updating obsolete `skipped_parents` expectations to collision expectations.

- [ ] **Step 7: Run full suite and commit**

```bash
python3 -m pytest -q
git add src/fluka/queue/collect_results.py tests/queue/test_collect_results.py
git commit -m "fix(queue): prevent ROOT result overwrite"
```

### Task 3: Stop Analysis After Collection Failure

**Files:**
- Modify: `src/fluka/cli/submit.py`
- Modify: `tests/run/test_orchestrator.py`

**Interfaces:**
- Consumes: `collect_results.main(Path) -> int`, `orchestrator.analyze_phase()`.
- Produces: `CollectionError(RuntimeError)` and fail-fast collect/analyze sequencing.

- [ ] **Step 1: Write failing orchestration test**

Add:

```python
def test_analyze_phase_stops_when_collection_fails(monkeypatch):
    analyzed = []
    monkeypatch.setattr("fluka.cli.submit.collect_sim", lambda sim: (_ for _ in ()).throw(
        RuntimeError("collection failed")
    ))
    monkeypatch.setattr("fluka.cli.analysis.run_sim", lambda sim: analyzed.append(sim))

    with pytest.raises(RuntimeError, match="collection failed"):
        orchestrator.analyze_phase(Path("sim.yaml"))

    assert analyzed == []
```

- [ ] **Step 2: Write failing `collect_sim` return-code test**

Add to `tests/run/test_cli_dispatch.py`:

```python
def test_collect_sim_raises_on_nonzero_result(monkeypatch):
    monkeypatch.setattr(submit, "resolve", lambda path, tool: {"output": "/runs"})
    monkeypatch.setattr("fluka.queue.collect_results.main", lambda path: 1)

    with pytest.raises(submit.CollectionError, match="collection failed"):
        submit.collect_sim(Path("sim.yaml"))
```

- [ ] **Step 3: Verify tests are red**

Run: `python3 -m pytest tests/run/test_orchestrator.py tests/run/test_cli_dispatch.py -q`

Expected: FAIL because non-zero collection result is ignored and `CollectionError` is absent.

- [ ] **Step 4: Implement fail-fast boundary**

Add `CollectionError`, check returned status in `collect_sim()`, and raise on non-zero. Keep `analyze_phase()` ordering unchanged; exception naturally prevents analysis.

- [ ] **Step 5: Verify and commit**

```bash
python3 -m pytest tests/run/test_orchestrator.py tests/run/test_cli_dispatch.py -q
python3 -m pytest -q
git add src/fluka/cli/submit.py tests/run/test_orchestrator.py tests/run/test_cli_dispatch.py
git commit -m "fix(run): stop analysis after collect failure"
```

### Task 4: Preserve FLUKA Exit Status Across Backends

**Files:**
- Modify: `src/fluka/queue/backends/slurm.py`
- Modify: `src/fluka/queue/backends/lsf.py`
- Modify: `src/fluka/queue/backends/htcondor.py`
- Modify: `src/fluka/queue/backends/ts.py`
- Modify: `tests/queue/backends/test_slurm.py`
- Modify: `tests/queue/backends/test_lsf.py`
- Modify: `tests/queue/backends/test_htcondor.py`
- Modify: `tests/queue/backends/test_htcondor_status.py`
- Modify: `tests/queue/backends/test_ts.py`

**Interfaces:**
- Consumes: backend `generate_script()`, `submit()`, `_sentinel_path()`.
- Produces: scripts that write sentinel and exit with FLUKA code; correct HTCondor sentinel lookup.

- [ ] **Step 1: Write failing script-contract tests**

For each generated shell script assert ordered presence of:

```python
assert "rc=$?" in content
assert "FLUKA_STATUS rc=$rc" in content
assert 'exit "$rc"' in content
```

For Task Spooler, inspect submitted `bash -c` command through patched `subprocess.run` and assert same fragments.

- [ ] **Step 2: Write failing HTCondor sentinel test**

Replace current stdout-based expectation with:

```python
def test_sentinel_path_uses_transferred_status_file(tmp_path):
    job = _job(run_dir=tmp_path, output="job.out")
    assert HTCondorBackend()._sentinel_path(job) == tmp_path / ".fluka_status"
```

Add a `job_state()` test with missing `condor_q` and `.fluka_status` containing `FLUKA_STATUS rc=1`; expect `FAIL`.

- [ ] **Step 3: Verify backend tests are red**

Run: `python3 -m pytest tests/queue/backends -q`

Expected: failures for missing `exit`, wrong `$?` variable form, and wrong HTCondor path.

- [ ] **Step 4: Implement shell exit-code contract**

Each runner executes FLUKA, immediately assigns `rc=$?`, writes sentinel with `$rc`, performs cleanup/transfer, and finishes with `exit "$rc"`. Change HTCondor `_sentinel_path()` to `Path(job.run_dir) / ".fluka_status"`.

- [ ] **Step 5: Verify and commit**

```bash
python3 -m pytest tests/queue/backends -q
python3 -m pytest -q
git add src/fluka/queue/backends tests/queue/backends
git commit -m "fix(queue): propagate FLUKA exit status"
```

### Task 5: Centralize Backend Registry and Typed Configuration

**Files:**
- Create: `src/fluka/queue/backends/registry.py`
- Modify: `src/fluka/queue/core/config.py`
- Modify: `src/fluka/queue/backends/base.py`
- Modify: `src/fluka/queue/launch_jobs.py`
- Modify: `src/fluka/grid/backends/queue_adapter.py`
- Modify: `src/fluka/cli/status.py`
- Modify: `tests/queue/core/test_config.py`
- Modify: `tests/grid/test_queue_adapter.py`
- Modify: `tests/run/test_status_cli.py`

**Interfaces:**
- Produces: `BACKEND_TYPES`, `new_backends()`, `SubmissionConfig`, `load_submission_config()`, `submission_config_from_view()`.
- Consumes: existing backend classes and unchanged YAML keys.

- [ ] **Step 1: Write failing registry parity test**

```python
def test_registry_exposes_all_supported_backends():
    assert set(BACKEND_TYPES) == {"ts", "slurm", "lsf", "condor"}
    instances = new_backends()
    assert set(instances) == set(BACKEND_TYPES)
    assert all(isinstance(instances[name], cls) for name, cls in BACKEND_TYPES.items())
```

- [ ] **Step 2: Verify registry test is red**

Run: `python3 -m pytest tests/queue/backends/test_base.py::test_registry_exposes_all_supported_backends -q`

Expected: import failure because registry does not exist.

- [ ] **Step 3: Create registry**

Implement:

```python
BACKEND_TYPES: dict[str, type[QueueBackend]] = {
    "ts": TSBackend,
    "slurm": SlurmBackend,
    "lsf": LSFBackend,
    "condor": HTCondorBackend,
}

def new_backends() -> dict[str, QueueBackend]:
    return {name: backend_type() for name, backend_type in BACKEND_TYPES.items()}
```

Migrate grid adapter, status, and legacy launcher to this source.

- [ ] **Step 4: Write failing typed-config equivalence tests**

Build equivalent mappings through legacy YAML and merged-view constructors, then assert:

```python
assert legacy.backend == merged.backend == "slurm"
assert legacy.input == merged.input
assert legacy.njobs == merged.njobs == 3
assert legacy.mem == merged.mem == "2400"
assert legacy.time == merged.time == "2-00:00:00"
assert legacy.dry_run is False and merged.dry_run is False
```

Also assert both values are `SubmissionConfig`, not `Namespace`.

- [ ] **Step 5: Verify typed-config tests are red**

Run: `python3 -m pytest tests/queue/core/test_config.py -q`

Expected: FAIL because existing constructors return `Namespace`.

- [ ] **Step 6: Implement `SubmissionConfig`**

Create this slots dataclass:

```python
@dataclass(slots=True)
class SubmissionConfig:
    backend: str
    input: str
    njobs: int
    custom_exe: str | None = None
    use_dpm: bool = False
    dry_run: bool = False
    output_dir: str | None = None
    nprim: int | None = None
    queue: str | None = None
    mem: str = "1500"
    ntasks: int = 1
    nodes: int = 1
    time: str | int = "1-00:00:00"
    gres: str = "disk:1G"
    farm_out: str = "/farm_out"
    ncpu: int = 1
    disk: int = 100000
    transfer_files: str = "yes"
    stdout: str = "job_$(Cluster)_$(Process).out"
    stderr: str = "job_$(Cluster)_$(Process).err"
    log: str = "job_$(Cluster)_$(Process).log"
```

Parse direct CLI `Namespace` once with `SubmissionConfig.from_mapping(vars(namespace))`. Map legacy Condor keys `output` and `error` to `stdout` and `stderr`. Replace parser-derived core objects with typed constructors while retaining current backend defaults and YAML key interpretation.

- [ ] **Step 7: Migrate backend type hints and callers**

Use `TYPE_CHECKING` imports in `base.py` to avoid cycles. Backends accept `SubmissionConfig`. Replace backend-test `_args()` helpers with explicit `SubmissionConfig(backend=..., input="sim.inp", njobs=1, ...)` values. Keep `argparse.Namespace` only inside parser tests and convert it before calling core code.

- [ ] **Step 8: Verify and commit**

```bash
python3 -m pytest tests/queue/core/test_config.py tests/grid/test_queue_adapter.py tests/run/test_status_cli.py -q
python3 -m pytest -q
git add src/fluka/queue src/fluka/grid/backends/queue_adapter.py src/fluka/cli/status.py tests
git commit -m "refactor(queue): unify backend configuration"
```

### Task 6: Extract Submission Service and Report Partial Failure

**Files:**
- Create: `src/fluka/queue/service.py`
- Modify: `src/fluka/queue/launch_jobs.py`
- Modify: `src/fluka/grid/backends/queue_adapter.py`
- Modify: `tests/queue/test_launch_jobs.py`
- Modify: `tests/queue/test_seed_uniqueness.py`
- Create: `tests/queue/test_service.py`

**Interfaces:**
- Consumes: `SubmissionConfig`, `new_backends()`, filesystem and seed helpers.
- Produces: `PreparedJob`, `SubmissionFailure`, `SubmissionSummary`, `SubmissionBatchError`, `prepare_jobs(config, fluka_path)`, `submit_prepared(config, prepared, backend)`, and `submit_jobs(config, fluka_path, backends=None)`.

- [ ] **Step 1: Write failing partial-failure test**

```python
def test_submit_prepared_attempts_all_jobs_then_raises(tmp_path):
    class FakeBackend:
        def __init__(self):
            self.calls = 0

        def generate_script(self, job_info, job_dir, config):
            return str(Path(job_dir) / "job.sh")

        def submit(self, script_path, job_info, config):
            self.calls += 1
            if job_info.iteration == 2:
                raise RuntimeError("queue down")
            return f"job {job_info.iteration}"

    config = SubmissionConfig(backend="ts", input="sim.inp", njobs=3, dry_run=True)
    prepared = [
        PreparedJob(i, tmp_path / f"job_{i:04d}", JobInfo("sim.inp", i, "/fluka", None))
        for i in (1, 2, 3)
    ]
    backend = FakeBackend()

    with pytest.raises(SubmissionBatchError) as exc:
        submit_prepared(config, prepared, backend)

    assert backend.calls == 3
    assert [failure.iteration for failure in exc.value.failures] == [2]
```

- [ ] **Step 2: Verify partial-failure test is red**

Run: `python3 -m pytest tests/queue/test_service.py::test_submit_prepared_attempts_all_jobs_then_raises -q`

Expected: import failure because service does not exist.

- [ ] **Step 3: Write failing working-directory test**

```python
def test_ts_adapter_does_not_change_process_cwd(tmp_path, monkeypatch):
    run_dir = tmp_path / "run_0001"
    run_dir.mkdir()
    (run_dir / "simulation.inp").write_text("RANDOMIZ 1. 1.\n")
    observed = []

    def observe_cwd(self, script_path, job_info, config):
        observed.append(Path.cwd())
        return "1"

    monkeypatch.setattr(queue_adapter.TSBackend, "submit", observe_cwd)
    before = Path.cwd()
    queue_adapter.submit_run(
        "ts", _config("ts"), run_dir, "simulation.inp", 1, "/fluka", False
    )

    assert observed == [before]
    assert Path.cwd() == before
```

- [ ] **Step 4: Verify working-directory test is red or exposes redundant mutation**

Run: `python3 -m pytest tests/grid/test_queue_adapter.py::test_ts_adapter_does_not_change_process_cwd -q`

Expected: FAIL because observer records `run_dir` instead of original working directory.

- [ ] **Step 5: Implement service and remove global `chdir`**

Move preparation, duplicate-seed guard, backend submission loop, and failure aggregation from `_execute_jobs()` into `submit_jobs()`. Remove `os.chdir()` from queue adapter because `TSBackend.submit()` already emits command-local `cd` for absolute inputs.

- [ ] **Step 6: Keep CLI behavior at boundary**

`launch_jobs.py` catches `SubmissionBatchError`, logs one line per failed iteration, and exits non-zero only from `main()`. Folder and benchmark modes count batch errors. Remove module-import `logging.basicConfig`; configure logging in `main()`.

- [ ] **Step 7: Verify and commit**

```bash
python3 -m pytest tests/queue/test_service.py tests/queue/test_launch_jobs.py tests/queue/test_seed_uniqueness.py tests/grid/test_queue_adapter.py -q
python3 -m pytest -q
git add src/fluka/queue/service.py src/fluka/queue/launch_jobs.py src/fluka/grid/backends/queue_adapter.py tests
git commit -m "refactor(queue): extract submission service"
```

### Task 7: Tighten Core Error Boundaries

**Files:**
- Modify: `src/fluka/queue/launch_jobs.py`
- Modify: `src/fluka/run/orchestrator.py`
- Modify: `src/fluka/cli/submit.py`
- Modify: `tests/queue/test_launch_jobs.py`
- Modify: `tests/run/test_orchestrator.py`

**Interfaces:**
- Consumes: typed config and submission service from Tasks 5-6.
- Produces: core exceptions with `SystemExit` restricted to CLI `main()` functions.

- [ ] **Step 1: Write failing core-boundary tests**

```python
def test_run_submission_raises_validation_error_instead_of_system_exit(config):
    config.input = "not-an-input.txt"
    with pytest.raises(ValueError, match="must end with .inp"):
        run_submission(config)
```

Add tests showing `main()` translates that exception to exit code `1`, while `run_submission()` never raises `SystemExit`.

- [ ] **Step 2: Verify tests are red**

Run: `python3 -m pytest tests/queue/test_launch_jobs.py -q`

Expected: FAIL because current `run_from_args()` calls `sys.exit()`.

- [ ] **Step 3: Replace core exits and broad catches**

Rename core entry to `run_submission(config: SubmissionConfig)`. Raise `ValueError`, `RuntimeError`, or domain errors. Catch only expected validation, filesystem, and scheduler errors in CLI loops. Keep unexpected exceptions visible.

- [ ] **Step 4: Verify and commit**

```bash
python3 -m pytest tests/queue/test_launch_jobs.py tests/run/test_orchestrator.py -q
python3 -m pytest -q
git add src/fluka/queue/launch_jobs.py src/fluka/run/orchestrator.py src/fluka/cli/submit.py tests
git commit -m "refactor(cli): isolate process exit handling"
```

### Task 8: Repair Public Documentation and Package Metadata

**Files:**
- Modify: `.gitignore`
- Modify: `README.md`
- Modify: `wiki/Home.md`
- Modify: `wiki/fluka-submit.md`
- Modify: `wiki/fluka-analysis.md`
- Modify: `wiki/fluka-compile.md`
- Modify: `pyproject.toml`
- Track and modify: `scripts/sync-wiki.sh`
- Modify: `tests/test_wheel_package.py`

**Interfaces:**
- Consumes: existing public CLI names and Git `origin`.
- Produces: truthful docs, complete package metadata, configurable wiki sync.

- [ ] **Step 1: Write failing metadata test**

Add TOML assertions:

```python
text = Path("pyproject.toml").read_text()
assert 'readme = "README.md"' in text
assert 'Repository = "https://github.com/AntoninoFulci/FlukaToolkit"' in text
assert "license =" not in text
```

- [ ] **Step 2: Verify metadata test is red**

Run: `python3 -m pytest tests/test_wheel_package.py::test_project_metadata_is_complete -q`

Expected: FAIL because `readme` and URLs are absent.

- [ ] **Step 3: Update metadata and documentation**

Add `readme = "README.md"` and Repository/Issues URLs. Remove public claims that ignored `docs/legacy/` ships in repository. Update old standalone-project wording to current package names. Do not add license metadata.

- [ ] **Step 4: Make wiki sync reproducible**

Stop ignoring entire `scripts/` directory; ignore `scripts/private/` instead. In `sync-wiki.sh`, resolve remote with:

```bash
WIKI_REMOTE="${FLUKATOOLKIT_WIKI_REMOTE:-}"
if [[ -z "$WIKI_REMOTE" ]]; then
    ORIGIN="$(git -C "$REPO_ROOT" remote get-url origin 2>/dev/null || true)"
    if [[ -z "$ORIGIN" ]]; then
        echo "Cannot resolve wiki remote: set FLUKATOOLKIT_WIKI_REMOTE." >&2
        exit 2
    fi
    WIKI_REMOTE="${ORIGIN%.git}.wiki.git"
fi
```

Validate with `bash -n scripts/sync-wiki.sh` and a temporary Git repository with a fake origin.

- [ ] **Step 5: Verify and commit**

```bash
python3 -m pytest tests/test_wheel_package.py -q
bash -n scripts/sync-wiki.sh
python3 -m pytest -q
git add .gitignore README.md wiki pyproject.toml scripts/sync-wiki.sh tests/test_wheel_package.py
git commit -m "docs: align repository metadata and wiki"
```

### Task 9: Add Local and CI Quality Gates

**Files:**
- Modify: `pyproject.toml`
- Create: `.github/workflows/ci.yml`
- Modify: Python files selected by Ruff formatting and lint fixes
- Modify: typed queue/run/CLI files required by mypy

**Interfaces:**
- Consumes: supported Python floor `>=3.10` and refactored modules.
- Produces: reproducible `ruff`, `mypy`, coverage, test, and wheel-build commands.

- [ ] **Step 1: Add development tools and configuration**

Set development extras to include `pytest>=8`, `pytest-cov>=5`, `build>=1`, `ruff>=0.8`, and `mypy>=1.13`. Add:

```toml
[tool.ruff]
target-version = "py310"
line-length = 100

[tool.ruff.lint]
select = ["E4", "E7", "E9", "F", "I", "UP"]

[tool.mypy]
python_version = "3.10"
files = ["src/fluka/queue", "src/fluka/run", "src/fluka/cli"]
ignore_missing_imports = true
check_untyped_defs = true
no_implicit_optional = true

[tool.coverage.run]
source = ["fluka"]

[tool.coverage.report]
show_missing = true
skip_covered = true
```

- [ ] **Step 2: Install development extras**

Run: `python3 -m pip install -e '.[dev]'`

Expected: tools install without changing runtime dependency set.

- [ ] **Step 3: Establish red quality checks**

Run:

```bash
ruff check src tests
ruff format --check src tests
mypy
```

Expected: initial lint, format, or typing failures identify exact cleanup required.

- [ ] **Step 4: Fix only reported violations**

Run `ruff check --fix src tests`, `ruff format src tests`, then make explicit typing corrections until `mypy` passes. Do not suppress project-owned errors globally.

- [ ] **Step 5: Create CI workflow**

Create `.github/workflows/ci.yml`:

```yaml
name: CI

on:
  push:
  pull_request:

jobs:
  test:
    runs-on: ubuntu-latest
    strategy:
      matrix:
        python-version: ["3.10", "3.12", "3.14"]
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: ${{ matrix.python-version }}
          cache: pip
      - run: python -m pip install -e '.[dev]'
      - run: ruff check src tests
      - run: ruff format --check src tests
      - run: mypy
      - run: pytest --cov=fluka --cov-report=term-missing -q
      - run: python -m build
```

No publish step.

- [ ] **Step 6: Run complete local gate**

```bash
ruff check src tests
ruff format --check src tests
mypy
python3 -m pytest --cov=fluka --cov-report=term-missing -q
python3 -m build
```

Expected: every command exits `0`.

- [ ] **Step 7: Commit**

```bash
git add pyproject.toml .github/workflows/ci.yml src tests
git commit -m "ci: enforce lint types tests and build"
```

### Task 10: Final Compatibility and Safety Verification

**Files:**
- Modify only if verification exposes a defect.
- Update: `graphify-out/` incrementally after code is final; directory remains ignored.

**Interfaces:**
- Verifies all outputs from Tasks 1-9.

- [ ] **Step 1: Verify registered commands and wheel contents**

Run:

```bash
python3 -m build
python3 -m pytest tests/test_wheel_package.py -q
```

Expected: wheel builds and contains six console scripts plus ROOT compiler assets.

- [ ] **Step 2: Verify full quality gate**

```bash
ruff check src tests
ruff format --check src tests
mypy
python3 -m pytest --cov=fluka --cov-report=term-missing -q
```

Expected: all commands exit `0`; no warning is hidden.

- [ ] **Step 3: Verify repository cleanliness**

Run:

```bash
git status --short --ignored
git diff --check
```

Expected: no generated build/cache artifact is staged or untracked; `graphify-out/` is ignored.

- [ ] **Step 4: Refresh project graph**

Run: `graphify update`

Expected: Graphify reflects registry, service, typed config, and new quality tooling without changing tracked source.

- [ ] **Step 5: Review commits and hand off**

Run: `git log --oneline --decorate -12`

Expected: separate cleanup, correctness, refactor, documentation, and CI commits; report any remaining legal decision as intentionally omitted license.
