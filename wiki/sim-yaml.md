# sim.yaml reference

`sim.yaml` is the "one config, many tools" file: a single YAML document with
up to four top-level sections — `grid`, `submit`, `analysis`, `root` — one
per command. This mapping is defined by `SECTIONS` in
`src/fluka/run/config.py`:

```python
SECTIONS = ("grid", "submit", "analysis", "root")
```

## The rule: each tool reads only its own section

Every CLI (`fluka-grid`, `fluka-submit`, `fluka-analysis`, `fluka-root`)
calls `fluka.cli._common.resolve_config(path, tool)`, which:

1. Loads the YAML file.
2. If it detects **other** `SECTIONS` keys in the file besides the current
   tool's, it treats the file as a multi-section `sim.yaml` and extracts
   just that tool's section (raising an error if the tool's own section is
   missing).
3. Otherwise it treats the whole file as a **standalone** config for that
   tool.

This means:

- A full `sim.yaml` with all four sections works with every command — each
  one silently ignores the sections it doesn't own.
- Each tool's **standalone** config format (a file whose top level *is*
  that tool's fields, no `grid:`/`submit:`/`analysis:`/`root:` wrapper)
  still works unchanged — full backward compatibility with the original
  per-project configs.
- `fluka-run <phase> <cfg>` (see [fluka-run](fluka-run)) always expects a
  multi-section file and dispatches each phase's own section to the
  corresponding tool.

## Section reference

### `grid` — read by [fluka-grid](fluka-grid)

Expands a parameter grid over a `.inp` template, patches unique seeds, and
submits each run.

| Key | Field | Meaning |
|-----|-------|---------|
| `fluka` | `input` | FLUKA `.inp` template. Relative paths resolve next to the config file. |
| `fluka` | `primaries` | Optional — overrides the `START` primary count. |
| `fluka` | `use_dpm` | `true` → `rfluka -d` (DPMJET/RQMD); exclusive with `custom_executable`. |
| `fluka` | `custom_executable` | Optional path passed as `-e` to `rfluka`. |
| `fluka` | `rfluka_path` | Optional FLUKA bin dir override. |
| `output` | `directory` | Where per-combo run dirs + patched inputs are written. |
| `grid` | `parameters` | Map of `#define` key → list of values (Cartesian product). |
| `grid` | `runs_per_combo` | Independent runs per combination (unique seeds). |
| `execution` | `backend` | `ts` \| `slurm` \| `lsf` \| `condor`. |
| `execution` | `max_parallel` | `ts` slot count (local concurrency). |
| `execution` | `queue`, `mem`, `time`, `ntasks`, `nodes`, `gres`, `ncpu`, `disk`, `condor_max_runtime` | Cluster-backend-specific fields. |

### `submit` — read by [fluka-submit](fluka-submit)

Submits prepared FLUKA inputs to a batch backend.

| Field | Meaning |
|-------|---------|
| `backend` | `ts` \| `slurm` \| `lsf` \| `condor`. |
| `input` | FLUKA `.inp` file to submit; must end in `.inp`. |
| `njobs` | Number of independent jobs (one random seed each). |
| `mem` | Memory request (backend-dependent units/semantics). |
| `time` | Wall-time limit, format `D-HH:MM:SS` (SLURM/LSF) or seconds (HTCondor). |
| `custom_exe`, `use_dpm`, `output_dir`, `nprim`, `dry_run`, `queue`, `ntasks`, `nodes`, `gres`, `ncpu`, `disk` | Optional / backend-specific fields — see [fluka-submit](fluka-submit) for the full list and defaults. |

### `analysis` — read by [fluka-analysis](fluka-analysis)

Post-processes `RESNUCLEi` output into per-isotope activity/mass in an
Excel workbook.

| Field | Meaning |
|-------|---------|
| `directory` | Simulation directory containing `fort.<unit>`/`*.rnc` output. Must exist. |
| `units` | List of FLUKA RESNUCLEi unit numbers, e.g. `[21, 22, 23]`. |
| `volume` | Scoring volume in cm³. |
| `isotopes` | Map of `Z: A` (or `Z: [A1, A2, ...]` for multiple masses of the same element). |
| `output` | Excel filename (default `isotopes.xlsx`). |
| `executable` | FLUKA merge tool (default `usrsuw`). |

### `root` — read by [fluka-root](fluka-root)

Compiles the FLUKA ROOT-output routines under `src/root_output/` (drives
`src/root_output/Makefile`).

| Field | Meaning |
|-------|---------|
| `files` | List of source filenames to build: `FluLib.cpp` → `TTree`, `FluLibRNTuple.cpp` → `RNTuple`. |
| `format` | Shorthand used only if `files` is omitted: `rntuple` → `FluLibRNTuple.cpp`, otherwise → `FluLib.cpp`. |
| `name` | Optional output binary name (`NAME=`); defaults to the source filename without its extension. |

## Worked example

The full annotated example, from `examples/sim.yaml`:

```yaml
# FlukaToolkit — one file drives a whole simulation.
# Each CLI reads ONLY its own section; sections it does not own are ignored.
# You can also feed each tool its own standalone config (back-compat).

# ── fluka-grid : expand a parameter grid over a template, seed, and submit ──
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

# ── fluka-submit : submit prepared FLUKA inputs to a batch backend ──
submit:
  backend: ts                  # ts | slurm | lsf | condor
  input: template.inp
  njobs: 2
  mem: "1500"
  time: "1-00:00:00"

# ── fluka-analysis : RESNUCLEi → per-isotope activity/mass → Excel ──
analysis:
  directory: results/c1/run_0001
  units: [21, 22, 23]
  volume: 1000                 # cm³
  isotopes:                    # Z: A
    31: 70
    30: 69
  output: isotopes.xlsx

# ── fluka-root : compile FLUKA ROOT-output routines (src/root_output/Makefile) ──
root:
  files: [FluLibRNTuple.cpp]   # FluLib.cpp → TTree, FluLibRNTuple.cpp → RNTuple
  format: rntuple
```

Any tool can be pointed at this same file — `fluka-grid sim.yaml`,
`fluka-submit sim.yaml`, `fluka-analysis sim.yaml`, `fluka-root sim.yaml` —
and each will use only the section it owns. See [Home](Home) for the
typical end-to-end flow and [fluka-run](fluka-run) for the orchestrator
that sequences `grid` → `submit` and `collect` → `analysis` automatically.
