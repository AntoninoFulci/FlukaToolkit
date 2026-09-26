# fluka-compile

`fluka-compile <cfg>` compiles the FLUKA ROOT-output routines under
`src/fluka/root_output/` — a C++/ROOT library, adapted and simplified from
discussions on the [FLUKA Forum](https://fluka-forum.web.cern.ch/t/saving-the-output-as-root-file/2361)
and the [official FLUKA examples](http://www.fluka.org/fluka.php?id=examples&sub=example3),
that lets FLUKA write its output directly in ROOT format instead of the
usual binary dumps.

## Purpose

`src/fluka/root_output/Makefile` compiles a C++ library containing all the
variables and functions needed to save data inside `mgdraw.f`, and links it
with your compiled FLUKA Fortran user routines into a custom FLUKA
executable. Two ROOT data formats are supported:

- `src/fluka/root_output/src/FluLib.cpp` (default) — saves data using the
  standard ROOT `TTree` structure.
- `src/fluka/root_output/src/FluLibRNTuple.cpp` — saves data using the modern,
  high-performance ROOT `RNTuple` structure.

The routines are compiled using the FLUKA `fff` tool. By default the
Makefile links against all optional FLUKA libraries (deactivate them in the
Makefile if not needed). It also contains linker fixes for macOS.

*Tested and working with `ROOT 6.38.04` and `FLUKA 4-5.2` compiled with
`MacPorts gcc14.3.0_0` on `Darwin 25.4.0 arm64 (M4 Pro)`.*

## Structure of the produced ROOT file

Depending on the compilation choice, the library writes a file called
`dump.root` containing either `TTree` or `RNTuple` objects, organized as
follows.

### `RunSummary` (`SimulationSummary`)

Run-level information.

| Branch | Type | Meaning |
|--------|------|---------|
| `StartTime` | `std::time_t` (saved as integer) | Timestamp when the simulation started. |
| `TotEvents` | `Int_t` | Total number of events processed. |
| `AvgTime` | `Double_t` | Average time per event. |
| `TotTime` | `Double_t` | Total simulation time. |

### `Source`

Primary particle source information (one entry per primary, created on the
first `sourcefill` call).

| Branch | Type | Meaning |
|--------|------|---------|
| `NCase` | `Int_t` | Event / primary index. |
| `ParticleID` | `Int_t` | FLUKA particle code. |
| `EKin`, `P` | `Double_t` | Kinetic energy and momentum. |
| `Vx`, `Vy`, `Vz` | `Double_t` | Position of the source. |
| `Cx`, `Cy`, `Cz` | `Double_t` | Direction cosines. |
| `Weight` | `Double_t` | Statistical weight. |

### `Events`

Surface crossings / transport events (created on the first `treefill`
call).

| Branch | Type | Meaning |
|--------|------|---------|
| `NCase`, `SurfaceID`, `ParticleID` | `Int_t` | Event index, surface identifier, FLUKA particle code. |
| `ETot`, `P` | `Double_t` | Total energy and momentum. |
| `Vx`, `Vy`, `Vz` | `Double_t` | Interaction / tracking position. |
| `Cx`, `Cy`, `Cz` | `Double_t` | Direction cosines. |
| `Weight1`, `Weight2` | `Double_t` | Transport / scoring weights. |
| `MotherID`, `ProcessID` | `Int_t` | Parent track ID and process code. |
| `MotherETot` | `Double_t` | Total energy of the parent. |
| `MotherVx`, `MotherVy`, `MotherVz` | `Double_t` | Position of the parent interaction. |
| `UniqueID` | `Double_t` | Unique identifier for the step or track. |

### `DepEvents`

Energy-deposition events (subset of FLUKA `mgdraw` information, created on
the first `depfill` call).

| Branch | Type | Meaning |
|--------|------|---------|
| `NCase`, `RegionID`, `ICode`, `ParticleID` | `Int_t` | Event index, region, interaction/deposition code, FLUKA particle code. |
| `ETot`, `P` | `Double_t` | Total energy and momentum at deposition. |
| `Vx`, `Vy`, `Vz` | `Double_t` | Position of the deposition. |
| `Cx`, `Cy`, `Cz` | `Double_t` | Direction cosines. |
| `Weight1`, `Weight2` | `Double_t` | Statistical weights. |
| `MotherID`, `ProcessID` | `Int_t` | Parent track and process codes. |
| `MotherETot` | `Double_t` | Total energy of the parent. |
| `MotherVx`, `MotherVy`, `MotherVz` | `Double_t` | Position of the parent interaction. |

### `USDEvents`

Events from the `USERDUMP` / USDRAW-related routines (created on the first
`usdfill` call).

| Branch | Type | Meaning |
|--------|------|---------|
| `NCase`, `RegionID`, `ICode`, `ParticleID` | `Int_t` | — |
| `EKin`, `P` | `Double_t` | Kinetic energy and momentum. |
| `Vx`, `Vy`, `Vz` | `Double_t` | Position. |
| `Cx`, `Cy`, `Cz` | `Double_t` | Direction cosines. |
| `Weight` | `Double_t` | Statistical weight. |
| `MotherID` | `Int_t` | Parent track ID. |
| `MotherETot` | `Double_t` | Total energy of the parent. |

*All trees/ntuples are written and the file is closed automatically when
`fileclose` is called at the end of the FLUKA run.*

## Prerequisites

- [FLUKA](https://fluka.cern/) must be installed, with `fluka-config` on
  `PATH` (the Makefile calls `fluka-config --path`, `--compiler`,
  `--libpath`, `--lib`, `--dpmlib`, `--rqmdlib`, `--intobjs`).
- [ROOT](https://root.cern/) must be installed, with `root-config` on
  `PATH` (the Makefile calls `root-config --cflags`, `--libs`, `--glibs`).

You will need to add the following cards to your FLUKA input file (refer to
the [FLUKA manual](https://flukafiles.web.cern.ch/manual/index.html)):

1. `USRICALL` — leave empty.
2. `USROCALL` — leave empty.
3. `USERDUMP`:
   - **WHAT(1):** `100`
   - **WHAT(2):** unit number to use (e.g., `99`)
   - **WHAT(3):** what part of `mgdraw` to activate (usually `2` is enough)
   - **WHAT(4):** set to `1` if you want to activate `USDRAW` entries.

Use the functions defined in `src/fluka/root_output/src/FluLib.cpp` (or
`src/fluka/root_output/src/FluLibRNTuple.cpp`) inside the correct FLUKA user
routines. See `src/fluka/root_output/routines/usrini.f` and
`src/fluka/root_output/routines/usrout.f` for guidance.

## Building via `make`

`src/fluka/root_output/Makefile` selects the source file through `USE_RNTUPLE`
(`0` → `FluLib.cpp`/`TTree`, the default; `1` → `FluLibRNTuple.cpp`/`RNTuple`)
and names the output binary via `NAME` (default `rootfluka`). The compiled
Fortran objects default to `OBJS = usrini.o usrout.o mgdraw.o`.

```bash
cd src/fluka/root_output

# Standard TTree output (FluLib.cpp)
make

# Modern RNTuple output (FluLibRNTuple.cpp)
make USE_RNTUPLE=1

# Custom executable name and explicit Fortran objects
make NAME=myexecutable OBJS="mgdraw.o usrini.o usrout.o"
```

The binary is written to `src/fluka/root_output/RootFlukaExecutables/<NAME>`, and
intermediate `.o`/`.mod` files are cleaned up after a successful build.
Other targets:

```bash
make clean      # remove RootFlukaExecutables/<NAME>*, *.o, *.so, $(OBJS), rootfluka*
make cleanall   # wipe the entire RootFlukaExecutables/ directory
```

### Run FLUKA with the executable

```bash
rfluka -M 1 -e src/fluka/root_output/RootFlukaExecutables/rootfluka example.inp
```

## The `compilerf` helper

To make compiling easier from any working directory, a bash script,
`src/fluka/root_output/scripts/compilerf.sh`, is provided.

1. **Set up environment variables.** Add the directory containing the
   Makefile to your shell configuration file (`~/.bashrc` or `~/.zshrc`):
   ```bash
   export FLUKA_ROOT="/path/to/FlukaToolkit/src/fluka/root_output"
   ```
2. **Source the script:**
   ```bash
   source /path/to/FlukaToolkit/src/fluka/root_output/scripts/compilerf.sh
   ```

Available commands:

- **`compilerf`** — compiles routines from your current directory and saves
  the executable to the default `RootFlukaExecutables` folder.
  - Standard (TTree) usage:
    ```bash
    compilerf myexecname routine1.f routine2.f
    ```
  - RNTuple usage — add `--rntuple` to compile against `FluLibRNTuple.cpp`:
    ```bash
    compilerf --rntuple myexecname routine1.f routine2.f
    ```
- **`compilerf_clean`** — cleans the specific executable and its related
  objects:
  ```bash
  compilerf_clean myexecname
  ```
- **`compilerf_cleanall`** — cleans the entire `RootFlukaExecutables`
  directory:
  ```bash
  compilerf_cleanall
  ```

## Driving it from `fluka-compile`

`fluka-compile <cfg>` is a thin wrapper (`src/fluka/cli/compile.py`) that
drives `src/fluka/root_output/Makefile` on your behalf, so you don't have to `cd`
into `src/fluka/root_output` or remember the `USE_RNTUPLE`/`NAME`/`OBJS`
variables. `<cfg>` is a `sim.yaml` with a top-level `general:` section plus
a `custom_exe:` section — a dedicated config works too, as long as it
still carries its own `general:` section (the top-level `general` section
is always required — see [sim.yaml reference](sim-yaml)).

From `examples/simple/example.yaml`:

```yaml
custom_exe:
  rntuple: false  # false → FluLib (TTree); true → FluLibRNTuple (RNTuple)
```

The packaged `usrini.f`, `usrout.f`, and `mgdraw.f` routines are used when
`routines` is omitted.

Field reference:

| Field | Meaning |
|-------|---------|
| `rntuple` | `false` (default) → builds against `FluLib.cpp` (`TTree`); `true` → `FluLibRNTuple.cpp` (`RNTuple`). Controls `USE_RNTUPLE=<0\|1>`. |
| `use_defaults` | `true` (default) → the shipped `usrini.f`/`usrout.f`/`mgdraw.f` under `src/fluka/root_output/routines/` are always compiled in, and `routines:` entries only override-by-basename or add extras (see below). `false` → **only** the files listed in `routines:` are compiled — nothing is injected, so you're responsible for supplying working `usrini.f`/`usrout.f` yourself if you want `dump.root` to open/close correctly (a warning is printed to stderr if they're missing). |
| `routines` | List of `.f` routines. Under `use_defaults: true`, any entry whose basename matches a shipped default (`usrini.f`, `usrout.f`, `mgdraw.f`) **overrides** that default; anything else is an **extra** routine compiled alongside them. Under `use_defaults: false`, this list *is* the full set of routines compiled — verbatim, in the order given. Paths resolve relative to the config file's directory. |
| `exe_path` | Optional path to the compiled executable. Defaults to `<sim.yaml directory>/.fluka/fluka_custom_exe`. If relative, it resolves relative to the config file's directory (same rule as `routines`). |
| `name` | Optional intermediate binary name inside the build tree, passed as `NAME=` (default `rootfluka`). This is *not* the final `exe_path` — `fluka-compile` always copies the built binary to `exe_path` afterward. |

### `OBJS` under `use_defaults: true` vs `false`

`fluka-compile` resolves the routine list, then passes it to `make` as
`OBJS="<routine1>.o <routine2>.o ..."`:

- **`use_defaults: true` (default)** — the resolved list is always
  `[usrini.f, usrout.f, mgdraw.f]` (each individually overridable by a
  `routines:` entry with a matching basename) followed by any extra,
  non-matching `routines:` entries, in the order given. So
  `OBJS` is always `usrini.o usrout.o mgdraw.o [extra1.o extra2.o ...]`.
- **`use_defaults: false`** — the resolved list is exactly `routines:`,
  nothing more, nothing less, in the order given. `OBJS` mirrors that list
  one-to-one. No `usrini.o`/`usrout.o`/`mgdraw.o` are injected; if your
  `routines:` list doesn't provide equivalents, `dump.root` may not open or
  close correctly (a warning is printed, but the build still proceeds).

`fluka-compile` stages the resolved routine files into a temporary build
directory alongside a copy of the Makefile and `src/`, and runs:

```bash
make -C <build_dir> USE_RNTUPLE=<0|1> NAME=<name> OBJS="<resolved objects>"
```

For example (with `use_defaults: true`), `routines: [custom/mgdraw.f]` (with
`mgdraw.f` living next to the config file) overrides the shipped `mgdraw.f`
and leaves `usrini.f`/`usrout.f` at their defaults; an entry like
`extra_routine.f` would be appended as an additional compiled object
instead of overriding anything.

## Running it

```bash
fluka-compile sim.yaml
```

The compiled executable is copied to `exe_path` (chmod `755`). If it
already exists, `fluka-compile` **always force-rebuilds and overwrites it**
— it's meant to be run explicitly when you want a fresh build. (Compare
this with `fluka-run`'s auto-compile, below, which reuses an existing
`exe_path` unless `general.recompile: true`.)

## Auto-compile from `fluka-run`

If a `sim.yaml` has a `custom_exe:` section, `fluka-run <cfg>` compiles it
automatically before doing anything else, then passes the resulting
executable straight through as `rfluka -e <exe_path>` to whichever phase
runs next (grid or submit) — you never have to invoke `fluka-compile`
separately. Unlike the standalone `fluka-compile` command, this path only
rebuilds when `general.recompile: true`; otherwise, if `exe_path` already
exists, the cached binary is reused as-is. See [fluka-run](fluka-run) and
[sim.yaml reference](sim-yaml).
