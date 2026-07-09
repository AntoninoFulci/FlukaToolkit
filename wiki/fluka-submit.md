# fluka-submit

`fluka-submit <cfg>` submits prepared FLUKA `.inp` files to a batch backend —
**SLURM**, **LSF**, **HTCondor**, or **Task-Spooler (`ts`)** — from a single
unified CLI. It is backed by the `fluka.queue` package
(`src/fluka/queue/launch_jobs.py`), the successor to the standalone
FlukaQueueSub project.

Each job gets a distinct `RANDOMIZ` seed, so the runs it launches are
statistically independent and safe to combine downstream.

## `--grid`: grid-then-submit

```bash
fluka-submit --grid sim.yaml
```

The `--grid` flag runs the grid phase first (equivalent to `fluka-grid`)
and then submits the result — the same sequence `fluka-run submit`
performs (see [fluka-run](fluka-run)). Without `--grid`, `fluka-submit`
just submits whatever `submit:`/standalone config it is given.

```bash
# submit only (inputs already prepared)
fluka-submit sim.yaml

# grid + submit in one step
fluka-submit --grid sim.yaml
```

`<cfg>` may be a standalone submit config or a multi-section `sim.yaml`
containing a `submit:` section — see [sim.yaml reference](sim-yaml). When a
`sim.yaml` is passed, `fluka-submit` reads only its `submit:` section.

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
- **LSF**: `queue=production`, `mem=1500`, `ntasks=1`,
  `time=1-00:00:00` (max `4-00:00:00`).
- **HTCondor**: `queue=vanilla` (universe), `mem=1500`, `ncpu=1`,
  `disk=100000` (kB), `time=86400` s (`+MaxRuntime`, max `345600` = 4 days),
  `transfer-files=yes`.

**DPM:** set `use_dpm: true` in the config to launch with the DPMJET/RQMD
executable (`rfluka -d`); it is mutually exclusive with `custom_exe`
(`rfluka -e`).

## The `submit:` config section

From `examples/sim.yaml` (lines 23-28):

```yaml
submit:
  backend: ts                  # ts | slurm | lsf | condor
  input: template.inp
  njobs: 2
  mem: "1500"
  time: "1-00:00:00"
```

Field reference:

| Field | Meaning |
|-------|---------|
| `backend` | Required. One of `ts`, `slurm`, `lsf`, `condor`. |
| `input` | Required FLUKA input file; must end in `.inp`. |
| `njobs` | Required. Number of independent jobs (one random seed each); must be ≥ 1. |
| `custom_exe` | Optional path to a custom FLUKA executable, passed as `-e` to `rfluka`. Mutually exclusive with `use_dpm`. |
| `use_dpm` | Optional; launches with `rfluka -d`. |
| `output_dir` | Optional root directory for job subfolders (default: input name without `.inp`). |
| `nprim` | Optional primary-particle count that overwrites the `START` card; omit to keep the value in the `.inp`. |
| `dry_run` | Optional; build scripts and print commands without submitting. |
| `mem`, `time`, `queue`, `ntasks`, `nodes`, `gres`, `ncpu`, `disk` | Backend-specific fields (see the table above); accepted whether or not the backend uses them. |

Your FLUKA input file must contain a `RANDOMIZ` card — the launcher
rewrites its seed per job. A `START` card is required only if you override
the primary count with `nprim`.

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

## Collecting results

Once jobs finish, `fluka-run analyze` (or `fluka.queue.collect_results`
directly) gathers each job's `.root` files into a `root_files/` directory
per parent run, printing a table of the planned moves and asking for
confirmation before moving files and removing the emptied `job_*`
directories. Jobs with no `.root` file are flagged.

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

See also `docs/legacy/queue-README.md` for the original FlukaQueueSub CLI
documentation (`launch_jobs.py`, folder-of-configs mode, and benchmark
profiles), which this command's `submit:` section mirrors.
