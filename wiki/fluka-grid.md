# fluka-grid

`fluka-grid <cfg>` is the front end of the toolkit: it takes a FLUKA `.inp`
template, expands a parameter grid, patches every combination with a unique
`RANDOMIZ` seed, and submits each resulting run through the same batch
backends used by [fluka-submit](fluka-submit). It is backed by the
`fluka.grid` package (`src/fluka/grid/`).

`<cfg>` may be a standalone grid config (a file whose top level *is* the
`fluka:`/`output:`/`grid:`/`execution:` keys) or a multi-section `sim.yaml`
containing a `grid:` section — see [sim.yaml reference](sim-yaml). When a
`sim.yaml` is passed, `fluka-grid` reads only its `grid:` section and ignores
the rest.

## What it does

1. Loads and validates the config (`fluka.grid.config.load_config` /
   `validate_config`).
2. Expands the Cartesian product of `grid.parameters` into one directory per
   combination, and `grid.runs_per_combo` run directories inside each.
3. Patches the `.inp` template per run: substitutes each `#define <key>`
   with the combo's value, rewrites `RANDOMIZ` with a unique seed, and (if
   `fluka.primaries` is set) overwrites the `START` primary count.
4. Submits every generated run to the configured `execution.backend`.

Total jobs submitted = (product of all `grid.parameters` list lengths) ×
`grid.runs_per_combo`.

## The `grid:` config section

From `examples/sim.yaml` (lines 6-20):

```yaml
grid:
  fluka:
    input: template.inp        # FLUKA .inp template (needs a #define per grid key + RANDOMIZ/START)
    primaries: 10000           # optional — overrides the START primary count
    use_dpm: false             # true → rfluka -d (DPMJET/RQMD); exclusive with custom_executable
  output:
    directory: results/        # per-combo run dirs + patched inputs written here
  grid:
    parameters:                # each key MUST match a `#define <key>` in the template
      beame: [0.05, 0.1, 0.5]
      mat: [GALLIUM, TUNGSTEN]
    runs_per_combo: 5          # independent runs per combination (unique seeds)
  execution:
    backend: ts                # ts | slurm | lsf | condor
    max_parallel: 4            # ts slot count (local concurrency)
```

Field reference (`fluka.grid.config.Config` and friends):

| Section | Field | Meaning |
|---------|-------|---------|
| `fluka` | `input` | Path to the FLUKA `.inp` template. Relative paths resolve next to the config file. |
| `fluka` | `custom_executable` | Optional path passed to `rfluka` as `-e <exe>`. Mutually exclusive with `use_dpm`. |
| `fluka` | `rfluka_path` | Optional FLUKA bin dir override; if unset, discovered via `fluka-config --bin`. |
| `fluka` | `primaries` | Optional integer that overrides the `START` primary count. |
| `fluka` | `use_dpm` | `true` → launches with `rfluka -d` (DPMJET/RQMD executable). |
| `output` | `directory` | Root directory where per-combo run dirs and patched inputs are written. |
| `grid` | `parameters` | Map of `#define` key → list of values; the grid is the Cartesian product of all lists. |
| `grid` | `runs_per_combo` | Number of statistically independent runs (unique seeds) per combination. |
| `execution` | `backend` | `ts` (default) \| `slurm` \| `lsf` \| `condor`. |
| `execution` | `max_parallel` | Local task-spooler slot count (`ts -S`); cluster backends also accept `queue`, `mem`, `time`, `ntasks`, `nodes`, `gres`, `ncpu`, `disk`, `condor_max_runtime`. |

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
detected, submission aborts before any job is sent.

## DPM

Set `fluka.use_dpm: true` to launch with the DPMJET/RQMD executable
(`rfluka -d`). It is mutually exclusive with `fluka.custom_executable`
(`rfluka -e`) — setting both raises a config error.

## Running it

```bash
# standalone grid config
fluka-grid grid_config.yaml

# or driving a multi-section sim.yaml (reads only the grid: section)
fluka-grid sim.yaml
```

To generate the grid *and* submit it in one step, use
[`fluka-submit --grid`](fluka-submit) or `fluka-run submit`
(see [fluka-run](fluka-run)).
