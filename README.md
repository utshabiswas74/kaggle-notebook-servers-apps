# FusionFlows

> Next-Generation Face Manipulation & Neural Frame Interpolation Platform.

[![License](https://img.shields.io/badge/license-OpenRAIL--AS-green)](https://github.com/utshabiswas74/fusionflows-windows-apps)
[![Release](https://img.shields.io/github/v/release/utshabiswas74/fusionflows-windows-apps)](https://github.com/utshabiswas74/fusionflows-windows-apps/releases/latest)

---

## Overview

**FusionFlows** brings together advanced face manipulation (swapping, face enhancement, frame enhancement) and multi-threaded neural video frame interpolation (**FusionFlows RIFE 3.1 NCNN Engine**) into an intuitive, high-performance platform.

### Key Highlights
- **Integrated Neural Frame Booster**: Boost video smoothness to 2x, 4x, or 8x original FPS with authentic motion-compensated interpolation.
- **High-Fidelity Processors**: Face Swapper, Face Enhancer (GFPGAN), and Frame Enhancer (SPAN) working seamlessly out of the box.
- **Interactive Web Interface & CLI**: Launch the Gradio dashboard or script high-throughput batch jobs directly from the terminal.
- **All-in-One Windows Installer**: Single click installer with bundled dependencies (`ffmpeg`, `ffprobe`, `rife-ncnn-vulkan`, and neural weights).

---

## Download & Installation

### Windows (Recommended)
Download the standalone installer from the [Releases](https://github.com/utshabiswas74/fusionflows-windows-apps/releases/latest):
1. Download **`FusionFlows-Windows.exe`**.
2. Run the installer to setup FusionFlows on your machine.
3. Launch **FusionFlows** from your Desktop shortcut or Start Menu.

---

## Usage

### Running via Executable
```cmd
FusionFlows.exe run
```

### Running from Source
```bash
python fusionflows.py run
```

### Command Line Options
```
options:
  -h, --help                                      show this help message and exit
  -v, --version                                   show program's version number (FusionFlows 3.9.1)

commands:
  run                                             run the interactive web UI
  headless-run                                    run headless processing
  batch-run                                       run batch mode
  force-download                                  force model downloads and exit
  benchmark                                       benchmark performance
  job-run                                         run a queued job
```

---

## Configuration & Defaults

FusionFlows uses `fusionflows.ini` for default application settings:
- **Processors**: `face_swapper`, `face_enhancer`, `frame_enhancer`
- **Target FPS Multiplier**: `2x` (automatic neural interpolation)
- **Output Video Scale**: `2.0`
- **Face Mask Types**: `box`, `occlusion`, `area`, `region`
- **Output Directory**: Saved automatically to your `Downloads` folder.

---

## License

This project is licensed under the OpenRAIL-AS License.
