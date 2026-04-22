# FlukaROOTOutput

With this code is possibile to compile and executable that produces a FLUKA output in ROOT format. The code is adapted and simplified from here https://fluka-forum.web.cern.ch/t/saving-the-output-as-root-file/2361 and here http://www.fluka.org/fluka.php?id=examples&sub=example3.

![alt text](ExampleROOTFiles.png)

The Makefile compile a C++ file called `Flulib.cpp` that contains all the variables needed to save almost everything inside `mgdraw.f`. The Makefile compile the routines using FLUKA `fff` tool. By default it will compile using all the optional FLUKA libraries, consider deactivating them if not needed. It also contains various fixes for MacOs, considering removing them when unecessary.

Tested and working with `ROOT 6.32.02` and `FLUKA 4-4.1` compiled with `MacPorts gcc12.4.0_1` on `Darwin 23.6.0 arm64 (M1)`.

### Structure of the produced ROOT file

The library writes a file called `dump.root` containing several `TTree` objects:

- **`RunSummary` (`SimulationSummary`)**

  - Stores run‑level information.
  - Branches and types:
    - `StartTime` (`std::time_t`, saved as integer) – timestamp when the simulation started.
    - `TotEvents` (`Int_t`) – total number of events processed.
    - `AvgTime` (`Double_t`) – average time per event.
    - `TotTime` (`Double_t`) – total simulation time.
- **`Source`** – primary particle source information (one entry per primary).

  - Branches and types (all created the first time `sourcefill` is called):
    - `NCase` (`Int_t`) – event / primary index.
    - `ParticleID` (`Int_t`) – FLUKA particle code.
    - `EKin`, `P` (`Double_t`) – kinetic energy and momentum.
    - `Vx`, `Vy`, `Vz` (`Double_t`) – position of the source.
    - `Cx`, `Cy`, `Cz` (`Double_t`) – direction cosines.
    - `Weight` (`Double_t`) – statistical weight.
- **`Events`** – surface crossings / transport events.

  - Branches and types (created on first `treefill`):
    - `NCase`, `SurfaceID`, `ParticleID` (`Int_t`) – event index, surface identifier, FLUKA particle code.
    - `ETot`, `P` (`Double_t`) – total energy and momentum.
    - `Vx`, `Vy`, `Vz` (`Double_t`) – interaction / tracking position.
    - `Cx`, `Cy`, `Cz` (`Double_t`) – direction cosines.
    - `Weight1`, `Weight2` (`Double_t`) – transport / scoring weights.
    - `MotherID`, `ProcessID` (`Int_t`) – parent track ID and process code.
    - `MotherETot` (`Double_t`) – total energy of the parent.
    - `MotherVx`, `MotherVy`, `MotherVz` (`Double_t`) – position of the parent interaction.
    - `UniqueID` (`Double_t`) – unique identifier for the step or track.
- **`DepEvents`** – energy‑deposition events (subset of FLUKA `mgdraw` information).

  - Branches and types (created on first `depfill`):
    - `NCase` (`Int_t`) – event index.
    - `RegionID` (`Int_t`) – region identifier.
    - `ICode` (`Int_t`) – deposition / interaction code.
    - `ParticleID` (`Int_t`) – FLUKA particle code.
    - `ETot`, `P` (`Double_t`) – total energy and momentum at deposition.
    - `Vx`, `Vy`, `Vz` (`Double_t`) – position of the deposition.
    - `Cx`, `Cy`, `Cz` (`Double_t`) – direction cosines.
    - `Weight1`, `Weight2` (`Double_t`) – statistical weights.
    - `MotherID`, `ProcessID` (`Int_t`) – parent track and process codes.
    - `MotherETot` (`Double_t`) – total energy of the parent.
    - `MotherVx`, `MotherVy`, `MotherVz` (`Double_t`) – position of the parent interaction.
- **`USDEvents`** – events from the `USERDUMP` / USDRAW‑related routines.

  - Branches and types (created on first `usdfill`):
    - `NCase` (`Int_t`) – event index.
    - `RegionID` (`Int_t`) – region identifier.
    - `ICode` (`Int_t`) – interaction / scoring code.
    - `ParticleID` (`Int_t`) – FLUKA particle code.
    - `EKin`, `P` (`Double_t`) – kinetic energy and momentum.
    - `Vx`, `Vy`, `Vz` (`Double_t`) – position.
    - `Cx`, `Cy`, `Cz` (`Double_t`) – direction cosines.
    - `Weight` (`Double_t`) – statistical weight.
    - `MotherID` (`Int_t`) – parent track ID.
    - `MotherETot` (`Double_t`) – total energy of the parent.

All trees are written and the file is closed when `fileclose` is called at the end of the FLUKA run.

### Prerequisites

- Install [FLUKA](https://fluka.cern/).
- Install [ROOT](https://root.cern/).

Add the following cards to the input file (refer to the [FLUKA manual](https://flukafiles.web.cern.ch/manual/index.html)):

1. `USRICALL`: empty
2. `USROCALL`: empty
3. `USERDUMP`:
   1. W(1):100
   2. W(2): unit number to use (i.e. 99)
   3. W(3): what part of mgdraw to activate, usually `2` is enough
   4. W(4): rembember to set it to `1` if you want to activate entry USDRAWS

- Then use the function defined in `Flulib.cpp` inside the correct routines. Refer to the files inside `ExampleRoutines` on how to use them.

### Usage

1. Download the repo:
   `gh repo clone AntoninoFulci/FlukaROOTOutput`
2. Specifying the files to compile.
   Either by command line:
   `make NAME=executablename OBJS="mgdraw.o usrini.o usrout.o"`
   or inside the Makefile, in that case:
   `make`
3. Run fluka with the executable:
   `rfluka -M 1 -e RootFlukaExecutables/rootfluka example.inp`

### Utilities

1. Export the directory containing the Makefile on your shell (or at your `.*rc`) to 'FLUKA_ROOT'.
   Example:
   `export FLUKA_ROOT="this/dir"`
2. Source `compilerf.sh` on your shell (or at your `.*rc`).
   For `zsh`:
   `source path_to_repo/compilerf.sh`

This will add several functions to your shell:

- `compilerf`: this permits to compile routines while in another directory and save the executable in the default directory (`path_to_repo/RootFlukaExecutables`).
  Usage:
  `compilerf rootflukaname routine1.f routine2.f ecc.f`
- `compilerf_clean`: attempt to clean the executable with the name passed from the default directory where it was compiled.
  Usage:
  `compilerf rootflukaname`
- `compilerf_cleanall`:  clean the default directory of FlukaROOTOutput executables (`path_to_repo/RootFlukaExecutables`).
