# sodium64
A SNES emulator for the N64, written in assembly.

> **This fork:** `ironangelo/sodium64` is an experimental continuation focused on pushing Sodium64 toward higher fidelity, native-frame performance, and broader enhancement-chip support. The engineering roadmap is in [`docs/ROADMAP.md`](docs/ROADMAP.md) and the validation strategy is in [`docs/VALIDATION.md`](docs/VALIDATION.md).

### Overview
The goal of sodium64 is to be fast and accurate enough to at least make some SNES games playable on the N64. It handles
rendering entirely on the RSP in order to reduce load on the main CPU. I thought it would be fun to write something
specifically for older hardware in assembly, so sodium64 was born!

### Downloads
The latest build of sodium64 is automatically provided via GitHub Actions, and can be downloaded from the
[releases page](https://github.com/Hydr8gon/sodium64/releases).

### Usage
Place SNES ROMs with extension `.sfc`/`.smc` in the same folder as `sodium64.z64` and `rom-converter.py`. Run
`rom-converter.py` using [Python](https://www.python.org) to convert the SNES ROMs to N64 ROMs. The output ROMs will be
in a new folder called `out`.

Alternatively, some flashcarts support loading ROMs directly with a supplied emulator. If you have an EverDrive, copy
`sodium64.z64` to the `ED64/emu` folder on your SD card and rename it to `smc.v64`. SNES ROMs must be in headerless
`.smc` format to work this way; `rom-converter.py` can optionally convert input ROMs for this.

### Controls
|  **N64**  |   **SNES**   |
|:---------:|:------------:|
| C-Buttons |     ABXY     |
|   D-Pad   |    D-Pad     |
|    L/R    |     L/R      |
|    A/B    | Start/Select |
|   Start   |   Settings   |

### Contributing to this fork
This fork uses branches and pull requests as its normal development workflow. Risky architecture experiments should stay isolated until automated validation supports merging them. Real Nintendo 64 testing is reserved for milestone gates rather than required for every small change; see [`docs/VALIDATION.md`](docs/VALIDATION.md).

The upstream project is maintained independently by Hydr8gon and has its own contribution policy.

### Building
Although sodium64 is written in assembly, it relies on [libdragon](https://github.com/DragonMinded/libdragon.git) for
its build system. With that set up, run `make` in the project root directory to start building.

### Hardware References
* [Fullsnes](https://problemkaputt.de/fullsnes.htm) - The main source of information on SNES hardware
* [Anomie Docs](https://www.romhacking.net/community/548) - More detailed documentation for certain components
* [6502 Tutorials](http://6502.org/tutorials/) - Has articles thoroughly covering the CPU and its quirks
* [bsnes](https://github.com/bsnes-emu/bsnes) - Reference for the HLE DSP-1 coprocessor commands

### Other Links
* [Hydra's Lair](https://hydr8gon.github.io) - Blog where I may or may not write about things
* [Discord Server](https://discord.gg/JbNz7y4) - A place to chat about my projects and stuff
