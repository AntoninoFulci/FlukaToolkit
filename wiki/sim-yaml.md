# sim.yaml reference (schema v2)

`sim.yaml` is the "one config, many tools" file. A single YAML document with a
shared **`general`** section plus one section per tool — `submit`, `grid`,
`custom_exe`, `analysis`. Every tool reads its own section and falls back to
`general` for anything shared.

## The rule: general provides the defaults, each section overrides

Every CLI resolves its config through `fluka.run.simconfig.resolve(path, tool)`,
which:

1. Loads the YAML file (a top-level `general` section is **required**).
2. Merges `general` as defaults, then the tool's own section on top (a key in
   the tool section wins over the same key in `general`).
3. Resolves path-valued keys (`input`, `output`, `custom_executable`,
   `rfluka_path`, `routines`) relative to the config file's directory.

Two extra rules make the shared config work cleanly:

- **grid also inherits `submit`.** The grid view is `general` → `submit` →
  `grid`, so `fluka-grid` reuses the batch resources declared once in `submit`
  (backend, `max_parallel`, `mem`, `time`, `farm_out`, …) — you never repeat
  them.
- **`analysis.output` never collides with `general.output`.** `general.output`
  is the results **directory**; `analysis.output` is the Excel **filename**.
  The loader keeps the shared dir separate internally, so the two never clash.

There is **no** old-schema fallback: the pre-v2 layout (`grid.fluka.input`,
`execution:`, `submit.backend`/`submit.input`, `root.files`/`root.format`) is
gone. The `root:` section from the early v2 layout has since been renamed to
`custom_exe:` (see below).

## `general` — shared by every tool

| Key | Meaning |
|-----|---------|
| `input` | FLUKA `.inp` file. One `#define <key>` per grid parameter + `RANDOMIZ`/`START`. |
| `backend` | `ts` \| `slurm` \| `lsf` \| `condor`. Used by grid + submit. |
| `output` | Results directory; per-combo run dirs are created under it. |
| `primaries` | Optional — overrides the `START` primary count. |
| `use_dpm` | Optional — `true` → `rfluka -d`; exclusive with `custom_executable`. |
| `custom_executable` | Optional — path passed as `-e` to `rfluka`. Set automatically by `fluka-run` when a `custom_exe:` section is present — see [fluka-compile](fluka-compile). |
| `rfluka_path` | Optional — explicit FLUKA bin dir. |
| `recompile` | Optional — `false` (default). When `fluka-run` auto-compiles a `custom_exe:` section, `true` forces a rebuild even if `exe_path` already exists; `false` reuses the cached binary. Has no effect on the standalone `fluka-compile` command, which always force-rebuilds. |

## `submit` — batch resources (read by [fluka-submit](fluka-submit) AND [fluka-grid](fluka-grid))

The single source of batch/scheduler settings. `fluka-submit` submits `njobs`
independent seeded jobs of `general.input`; `fluka-grid` reuses the same
resources for every grid run.

| Field | Meaning |
|-------|---------|
| `njobs` | Independent jobs (one random seed each) — submit-standalone only. |
| `max_parallel` | `ts` slot count (local concurrency). |
| `mem` | Memory request (MB; backend semantics vary). |
| `time` | Wall-time limit, `D-HH:MM:SS` (SLURM/LSF) or seconds (HTCondor). |
| `ntasks`, `nodes` | SLURM task/node counts. |
| `gres` | SLURM generic resources (e.g. `disk:1G`). |
| `ncpu`, `disk`, `condor_max_runtime` | HTCondor cpus / `request_disk` (kB) / `+MaxRuntime` (s). |
| `queue` | partition (SLURM) / queue (LSF) / universe (HTCondor). |
| `farm_out` | SLURM: accessible dir for out/err + the `fluka-status` sentinel (default `/farm_out`). |

## `grid` — read by [fluka-grid](fluka-grid)

| Field | Meaning |
|-------|---------|
| `parameters` | Map of `#define` key → list of values (Cartesian product). Each key MUST match a `#define <key>` in `general.input`. |
| `runs_per_combo` | Independent runs per combination (unique seeds). |

## `custom_exe` — read by [fluka-compile](fluka-compile)

Compiles the FLUKA ROOT-output executable. See [fluka-compile](fluka-compile)
for the routine-resolution rules. A `custom_exe:` section is optional — omit
it entirely if your simulation doesn't need a custom-compiled executable.
When present, `fluka-run` compiles it automatically before running the
grid/submit phase and passes the result through as `general.custom_executable`
(`rfluka -e <exe_path>`).

| Field | Meaning |
|-------|---------|
| `rntuple` | `false` (default) → `FluLib` (`TTree`); `true` → `FluLibRNTuple` (`RNTuple`). |
| `use_defaults` | `true` (default) → shipped `usrini.f`/`usrout.f`/`mgdraw.f` are always compiled in, with `routines:` entries overriding by basename or added as extras. `false` → only the files listed in `routines:` are compiled, verbatim. |
| `routines` | Optional list of `.f` routines. Under `use_defaults: true`, overrides the shipped defaults `usrini.f`/`usrout.f`/`mgdraw.f` by basename; anything else is an extra compiled alongside. Under `use_defaults: false`, this is the complete routine list. |
| `exe_path` | Optional path to the compiled executable. Defaults to `<sim.yaml directory>/.fluka/fluka_custom_exe` (gitignored build artifact). Relative paths resolve against the config file's directory. |
| `name` | Optional intermediate binary name (`NAME=`, default `rootfluka`) — internal to the build tree, not the final `exe_path`. |

## `analysis` — read by [fluka-analysis](fluka-analysis)

Post-processes `RESNUCLEi` output into per-isotope activity/mass in an Excel
workbook.

| Field | Meaning |
|-------|---------|
| `run` | Run subdirectory, relative to `general.output` (e.g. `c1/run_0001` → `results/c1/run_0001`). Must exist. |
| `units` | List of FLUKA RESNUCLEi unit numbers, e.g. `[21, 22]`. |
| `volume` | Scoring volume in cm³. |
| `isotopes` | Map of `Z: A` (or `Z: [A1, A2, ...]` for multiple masses of one element). |
| `output` | Excel filename (default `isotopes.xlsx`). |
| `executable` | FLUKA merge tool (default `usrsuw`). |

## Worked example

The full annotated example, from `examples/simple/example.yaml`:

```yaml
general:
  input: example.inp        # one #define per grid key + RANDOMIZ/START
  backend: ts               # ts | slurm | lsf | condor
  output: results/
  primaries: 1000
  use_dpm: false

submit:                     # batch resources — used by submit AND grid
  njobs: 2
  max_parallel: 10
  mem: "1500"
  time: "1-00:00:00"
  ntasks: 1
  nodes: 1
  gres: "disk:1G"
  ncpu: 1
  disk: 100000
  condor_max_runtime: 86400
  queue: null
  farm_out: /farm_out

grid:
  parameters:               # keys MUST match #define lines in example.inp
    irrtime: [86400, 172800]
    current: [6.24E+15, 6.24E+16]
    mat: [COPPER, TUNGSTEN]
  runs_per_combo: 2

custom_exe:
  rntuple: false
  # omit routines to use packaged usrini/usrout/mgdraw defaults

analysis:
  run: c1/run_0001          # -> results/c1/run_0001
  units: [21, 22]
  volume: 1000
  isotopes:
    31: 70
    30: 69
  output: isotopes.xlsx
```

Point any tool at this same file — `fluka-grid sim.yaml`,
`fluka-submit sim.yaml`, `fluka-compile sim.yaml`, `fluka-analysis sim.yaml`,
`fluka-status sim.yaml` — and each uses `general` plus only its own section.
See [Home](Home) for the end-to-end flow and [fluka-run](fluka-run) for the
orchestrator.
