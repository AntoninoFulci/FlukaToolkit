# fluka-status

`fluka-status <cfg>` reports the per-job state of a grid submission —
PENDING / RUNNING / DONE / FAIL / UNKNOWN — without you having to SSH in
and run `squeue`/`bjobs`/`condor_q` yourself. It closes the no-polling gap
called out in [fluka-run](fluka-run): `fluka-run submit` (and `fluka-grid`)
hand jobs off to the farm and return immediately, and previously the only
way to know when they were done was to check the batch system by hand.
It is backed by `fluka.run.status` and `fluka.run.manifest`
(`src/fluka/run/`).

## The manifest

Every job submitted through the grid path (`fluka-grid`, and
`fluka-run submit` / `fluka-submit --grid`, which run the grid phase) is
recorded in a manifest file written next to the run outputs:

```
<output.directory>/.fluka_manifest.json
```

Each entry captures the combo, run index/name, run directory, backend,
parsed job ID, input file, submission timestamp, and a small
backend-specific `extra` payload used to locate the job's output later
(see below). `fluka-status` reads this file — nothing else — to know which
jobs exist and where to look for them; if it's missing or empty,
`fluka-status` tells you to run `fluka-grid` / `fluka-run submit` first.

## The five states

| State | Meaning |
|-------|---------|
| `PENDING` | Job is queued but not yet running. |
| `RUNNING` | Job is executing (in the queue, active). |
| `DONE` | Job finished with exit code 0. |
| `FAIL` | Job finished with a non-zero exit code. |
| `UNKNOWN` | Job isn't in the queue and no completion sentinel was found. |

## Detection model

For each manifest entry, `fluka-status` asks the matching backend two
questions, in order:

1. **Live queue query** — is the job still known to the scheduler?
   (`squeue -j` for SLURM, `bjobs` for LSF, `condor_q` for HTCondor, `tsp -s`
   for Task-Spooler.) If so, the state is `PENDING` or `RUNNING`.
2. **Completion sentinel** — if the job is no longer in the queue, each
   backend's job script self-emits a one-line sentinel file after the FLUKA
   run exits:
   ```
   FLUKA_STATUS rc=$?
   ```
   `fluka-status` reads that file and reports `DONE` (`rc=0`) or `FAIL`
   (any other code). If neither the queue nor a sentinel gives an answer,
   the state is `UNKNOWN`.

Where the sentinel lives depends on the backend, since each writes to
whatever location is guaranteed accessible for it:

- **`ts`** — `<run_dir>/.fluka_status` (local filesystem, same host).
- **`lsf`** — `<run_dir>/.fluka_status`.
- **`condor`** — the job's configured `output` file pattern
  (`job_$(Cluster)_$(Process).out` by default), resolved relative to the
  run dir.
- **`slurm`** — **not** the run directory (compute nodes' local disk isn't
  guaranteed reachable from where you run `fluka-status`). Instead it's
  written under the cluster's shared `farm_out` directory:
  ```
  <farm_out>/<user>/<job_name>-<job_id>.fluka_status
  ```
  `farm_out` defaults to `/farm_out` and is set via the `execution.farm_out`
  config field (`fluka.grid.config.ExecutionConfig.farm_out`) or the
  SLURM backend's `--farm-out` CLI override — see
  [fluka-grid](fluka-grid) / [fluka-submit](fluka-submit).

## Usage

```bash
fluka-status sim.yaml               # one-shot table of every job's state
fluka-status sim.yaml --watch 30    # poll every 30s until all jobs are terminal
fluka-status sim.yaml --collect     # once all jobs are terminal, run collect+analyze
fluka-status sim.yaml --json        # emit JSON instead of a table
```

`--watch` with no value (`--watch` alone, no `SEC`) polls every 15 seconds.

`<cfg>` may be a standalone grid config or a multi-section `sim.yaml`
containing a `grid:` section, same as [fluka-grid](fluka-grid).

`--watch` (bare, or `--watch SEC`) re-queries and re-prints the table every
`SEC` seconds (default 15) until every job has reached a terminal state
(`DONE` or `FAIL`). `--collect`, once every job is terminal, refuses to
proceed if any job `FAIL`ed, and otherwise runs the same
collect-then-analyze step as `fluka-run analyze` — i.e. it is the
wait-then-analyze counterpart to `fluka-run submit`.

## v1 limitation: manifest recording is grid-path only

Manifest recording (`record_job`, in `src/fluka/grid/run.py`) is wired into
the **grid submission path** — `fluka-grid`, and `fluka-run submit` /
`fluka-submit --grid` (which run the grid phase before submitting). A plain
`fluka-submit sim.yaml` invocation, without `--grid`, does **not** currently
write manifest entries, so `fluka-status` has nothing to report for jobs
submitted that way. Wiring the standalone `fluka-submit` path into the
manifest is a follow-up.
