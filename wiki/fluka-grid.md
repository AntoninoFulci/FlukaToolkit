# fluka-grid

`fluka-grid <cfg>` is the front end of the toolkit: it takes a FLUKA `.inp`
template, expands a parameter grid, patches every combination with a unique
`RANDOMIZ` seed, and submits each resulting run through the same batch
backends used by [fluka-submit](fluka-submit). It is backed by the
`fluka.grid` package (`src/fluka/grid/`).

`<cfg>` is a `sim.yaml` with a top-level `general:` section plus a `grid:`
section — see [sim.yaml reference](sim-yaml). `fluka-grid` resolves its view
as `general` → `submit` → `grid` (it reuses `submit`'s batch resources, so
`max_parallel`/`mem`/`time`/`farm_out`/… never need to be repeated under
`grid:`), then reads only that merged view.

## What it does

1. Resolves the merged config via `fluka.run.simconfig.resolve(path, "grid")`
   and loads/validates it (`fluka.grid.config.load_config` /
   `validate_config`).
2. Expands the Cartesian product of `grid.parameters` into one directory per
   combination, and `grid.runs_per_combo` run directories inside each.
3. Patches the `.inp` template per run: substitutes each `#define <key>`
   with the combo's value, rewrites `RANDOMIZ` with a unique seed, and (if
   `general.primaries` is set) overwrites the `START` primary count.
4. Submits every generated run to the configured `general.backend`.

Total jobs submitted = (product of all `grid.parameters` list lengths) ×
`grid.runs_per_combo`.

## The `grid:` config section

From `examples/simple/example.yaml`:

```yaml
general:
  input: example.inp        # FLUKA .inp (needs a #define per grid key + RANDOMIZ/START)
  backend: ts                # ts | slurm | lsf | condor
  output: results/           # per-combo run dirs + patched inputs written here
  primaries: 1000            # optional — overrides the START primary count
  use_dpm: false              # true → rfluka -d (DPMJET/RQMD); exclusive with custom_executable

submit:                      # batch resources, reused by grid — see fluka-submit
  max_parallel: 10           # ts slot count (local concurrency)
  mem: "1500"
  time: "1-00:00:00"

grid:
  parameters:                # each key MUST match a `#define <key>` in example.inp
    irrtime: [86400, 172800]
    mat: [COPPER, TUNGSTEN]
  runs_per_combo: 2          # independent runs per combination (unique seeds)
```

Field reference (merged view consumed by `fluka.grid.config.Config` and
friends — see [sim.yaml reference](sim-yaml) for the full schema):

| Section | Field | Meaning |
|---------|-------|---------|
| `general` | `input` | Path to the FLUKA `.inp` template. Relative paths resolve next to the config file. |
| `general` | `custom_executable` | Optional path passed to `rfluka` as `-e <exe>`. Mutually exclusive with `use_dpm`. |
| `general` | `rfluka_path` | Optional FLUKA bin dir override; if unset, discovered via `fluka-config --bin`. |
| `general` | `primaries` | Optional integer that overrides the `START` primary count. |
| `general` | `use_dpm` | `true` → launches with `rfluka -d` (DPMJET/RQMD executable). |
| `general` | `output` | Root directory where per-combo run dirs and patched inputs are written. |
| `general` | `backend` | `ts` (default) \| `slurm` \| `lsf` \| `condor`. |
| `grid` | `parameters` | Map of `#define` key → list of values; the grid is the Cartesian product of all lists. |
| `grid` | `runs_per_combo` | Number of statistically independent runs (unique seeds) per combination. |
| `submit` | `max_parallel` | Local task-spooler slot count (`ts -S`); cluster backends also accept `queue`, `mem`, `time`, `ntasks`, `nodes`, `gres`, `ncpu`, `disk`, `condor_max_runtime`, `farm_out`. |

## Template requirements

`fluka-grid` patches an ordinary FLUKA `.inp` file. The template must
contain:

- A `#define NAME value` line for **every** grid parameter (the value is
  replaced per combination):
  ```
  #define beame 0.1
  #define mat   GALLIUM
  ```
- A `RANDOMIZ` card (rewritten per run with a unique seed):
  ```
  RANDOMIZ          1.0
  ```
- A `START` card (its primary count is overwritten when `fluka.primaries` is
  set):
  ```
  START         10000.
  ```

If a grid parameter has no matching `#define` in the template,
`validate_config` raises an error and submission aborts before anything is
generated or sent.

## What it produces

```
results/
└── beame0.05_matGALLIUM/         # one dir per parameter combination
    ├── run_0001/
    │   └── simulation_0001.inp    # patched template (combo values + unique seed)
    ├── run_0002/
    └── ...
```

Seeds are unique across the whole output directory; if a duplicate is
detected, `fluka-grid` reseeds the duplicate `.inp` files in place with
fresh unique seeds and continues submitting — it does not abort. (This
differs from the `fluka-submit` / `launch_jobs.py` path, which aborts on
duplicate seeds.)

## DPM

Set `fluka.use_dpm: true` to launch with the DPMJET/RQMD executable
(`rfluka -d`). It is mutually exclusive with `fluka.custom_executable`
(`rfluka -e`) — setting both raises a config error.

## Running it

```bash
# standalone grid config (still needs its own general: section)
fluka-grid grid_config.yaml

# or driving a full sim.yaml (reads general + submit, then only its own grid: section)
fluka-grid sim.yaml
```

To generate the grid *and* submit it in one step, use
[`fluka-submit --grid`](fluka-submit) or bare `fluka-run`
(see [fluka-run](fluka-run)).
