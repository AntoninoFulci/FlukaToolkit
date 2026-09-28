# fluka-submit

`fluka-submit <cfg>` submits prepared FLUKA `.inp` files to a batch backend —
**SLURM**, **LSF**, **HTCondor**, or **Task-Spooler (`ts`)** — from a single
unified CLI. It is backed by the `fluka.queue` package and its typed
submission service (`src/fluka/queue/service.py`).

Each job gets a distinct `RANDOMIZ` seed, so the runs it launches are
statistically independent and safe to combine downstream.

## `--grid`: grid-then-submit

```bash
fluka-submit --grid sim.yaml
```

The `--grid` flag runs the grid phase first (equivalent to `fluka-grid`)
and submits every generated run — the same sequence bare `fluka-run`
performs (see [fluka-run](fluka-run)). Without `--grid`, `fluka-submit`
submits the input described by the `general:` and `submit:` sections.

```bash
# submit only (inputs already prepared)
fluka-submit sim.yaml

# grid + submit in one step
fluka-submit --grid sim.yaml
```

`<cfg>` is a `sim.yaml` with a top-level `general:` section plus a
`submit:` section — see [sim.yaml reference](sim-yaml). `fluka-submit`
resolves its view as `general` → `submit`: `backend`/`input`/`output`/
`primaries`/`use_dpm`/`custom_executable`/`rfluka_path` come from
`general`, while `njobs` and the batch-resource fields (`mem`, `time`,
`queue`, `ntasks`, `nodes`, `gres`, `ncpu`, `disk`,
`condor_max_runtime`, `farm_out`, …) come from `submit`.

## Backends

| backend | notes |
|---------|-------|
| `ts` (default) | Task-Spooler; no extra options beyond the common ones. |
| `slurm` | Uses `queue`/`mem`/`ntasks`/`nodes`/`time`/`gres`. |
| `lsf` | Uses `queue`/`mem`/`ntasks`/`time`. |
| `condor` | Uses `queue`/`mem`/`ncpu`/`disk`/`time` (`+MaxRuntime`), plus `transfer-files`/`output`/`error`/`log`. |

All submission is delegated to per-backend adapters under
`src/fluka/queue/backends/`. Backend defaults (from the CLI argument
parsers):

- **SLURM**: `queue=production`, `mem=1500`, `ntasks=1`, `nodes=1`,
  `time=1-00:00:00` (max `4-00:00:00`), `gres=disk:1G`.
- **LSF**: `queue=normal`, `mem=1500`, `ntasks=1`,
  `time=1-00:00:00` (max `4-00:00:00`).
- **HTCondor**: `queue=vanilla` (universe), `mem=1500`, `ncpu=1`,
  `disk=100000` (kB), `time=86400` s (`+MaxRuntime`, max `345600` = 4 days),
  `transfer-files=yes`.

**DPM:** set `use_dpm: true` in the config to launch with the DPMJET/RQMD
executable (`rfluka -d`); it is mutually exclusive with `custom_exe`
(`rfluka -e`).

## The `general:` + `submit:` config sections

From `examples/simple/example.yaml`:

```yaml
general:
  input: example.inp        # FLUKA .inp (needs RANDOMIZ + a START card)
  backend: ts                # ts | slurm | lsf | condor
  output: results/           # job subfolders are created under here
  primaries: 1000            # optional — overrides the START primary count
  use_dpm: false              # true → rfluka -d (DPMJET/RQMD); exclusive with custom_executable

submit:                      # batch resources — the single source used by submit AND grid
  njobs: 2                   # independent seeded jobs of general.input
  mem: "1500"
  time: "1-00:00:00"
```

Field reference:

| Section | Field | Meaning |
|---------|-------|---------|
| `general` | `input` | Required FLUKA input file; must end in `.inp`. |
| `general` | `backend` | Required. One of `ts`, `slurm`, `lsf`, `condor`. |
| `general` | `output` | Root directory for job subfolders (default: input name without `.inp` if omitted). |
| `general` | `primaries` | Optional; overrides the `START` primary count. |
| `general` | `custom_executable` | Optional path to a custom FLUKA executable, passed as `-e` to `rfluka`. Mutually exclusive with `use_dpm`. |
| `general` | `use_dpm` | Optional; launches with `rfluka -d`. |
| `submit` | `njobs` | Required. Number of independent jobs (one random seed each); must be ≥ 1. |
| `submit` | `mem`, `time`, `queue`, `ntasks`, `nodes`, `gres`, `ncpu`, `disk`, `condor_max_runtime`, `farm_out` | Backend-specific fields (see the table above); accepted whether or not the backend uses them. |

Your FLUKA input file must contain a `RANDOMIZ` card — the launcher
rewrites its seed per job. A `START` card is required only if you override
the primary count with `general.primaries`.

## What it produces

Jobs are written under the output directory (default: the input name
without `.inp`):

```text
sim/
├── job_0001/
│   ├── sim_0001.inp        # per-job input, unique RANDOMIZ seed
│   ├── *.out                # FLUKA stdout
│   ├── *.err                # FLUKA stderr
│   ├── *.log                # HTCondor only
│   └── *.root                # FLUKA output (depends on the executable)
├── job_0002/
│   └── ...
└── ...
```

## Submission failures

Submission attempts every independently prepared job even when one scheduler call
fails. Each failed job is reported with its iteration and scheduler error; successful
submissions remain successful. After all jobs have been attempted, any failure makes
the command exit non-zero.

## Collecting results

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

## Checking seeds

Seed uniqueness is enforced at two points:

- **During launch** — a unique seed is allocated per job (including across
  re-launches into the same output directory), then the generated inputs are
  re-scanned on disk and submission **aborts before sending anything** if any
  duplicate is found.
- **After launch** — `fluka.queue.check_seeds` audits an existing set of
  runs on demand, scanning every `*/job_*/*.inp`, reporting duplicate seeds
  in a table, and exiting non-zero when duplicates are found (usable as a
  gate in scripts or CI).
