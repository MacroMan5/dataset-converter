# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/).

## [1.0.0] - 2026-03-18

### Added

- GUI mode with tkinter (no dependencies)
- CLI mode with argparse
- Auto-detection of class IDs from YOLO label files
- Export formats:
  - CVAT (Darknet YOLO 1.1)
  - Roboflow (YOLO folder)
  - YOLO Split (train/val with data.yaml)
- Support for `images/labels/` subdirectory and flat directory layouts
- `--no-labels` flag for exporting images only (fresh annotation)
- `--val-ratio` flag for YOLO split customization
- pip installable (`pip install dataset-converter`)
- `dataset-converter` console command
