<p align="center">
  <img src="icon.png" alt="Dataset Converter" width="128">
</p>

# Dataset Converter

Simple GUI tool to convert YOLO-format datasets into ready-to-import archives for annotation platforms.

![Python 3.8+](https://img.shields.io/badge/python-3.8+-blue.svg)
![No Dependencies](https://img.shields.io/badge/dependencies-none-green.svg)
[![PyPI](https://img.shields.io/pypi/v/dataset-converter)](https://pypi.org/project/dataset-converter/)
![License MIT](https://img.shields.io/badge/license-MIT-green.svg)

## Install

```bash
pip install dataset-converter
```

Or from source:

```bash
git clone https://github.com/MacroMan5/dataset-converter.git
cd dataset-converter
pip install .
```

## Features

- **Auto-detects class IDs** from your label files — you just name them
- **Zero dependencies** — pure Python + tkinter (included with Python)
- **GUI & CLI** modes
- Exports to:
  - **CVAT** (Darknet YOLO 1.1 — `obj.data`, `obj.names`, `train.txt`, `obj_train_data/`)
  - **Roboflow** (YOLO folder — `train/images/`, `train/labels/`, `data.yaml`)
  - **YOLO Split** (standard train/val split with `data.yaml`)

## Usage

### GUI

```bash
dataset-converter
```

1. **Browse** → select your dataset folder (with `images/` and `labels/` subfolders)
2. The tool scans your labels and shows detected class IDs → **name each class**
3. Pick your **output format** (CVAT, Roboflow, YOLO split)
4. Click **Convert** → get a ready-to-import `.zip`

### CLI

```bash
# Auto-detect classes (names default to class_0, class_1, ...)
dataset-converter --cli -i path/to/dataset -f cvat

# Name your classes explicitly
dataset-converter --cli -i path/to/dataset -f cvat -c dog cat bird

# Roboflow format
dataset-converter --cli -i path/to/dataset -f roboflow -c head player

# YOLO with 80/20 train/val split
dataset-converter --cli -i path/to/dataset -f yolo -c head player

# Export images only (no annotations) for fresh labeling
dataset-converter --cli -i path/to/dataset -f cvat --no-labels
```

## Expected Input Format

```
your_dataset/
├── images/
│   ├── img001.jpg
│   ├── img002.png
│   └── ...
├── labels/           # YOLO format: class_id x_center y_center width height
│   ├── img001.txt
│   ├── img002.txt
│   └── ...
└── meta/             # (optional, ignored by converter)
```

Also supports flat directories where images and labels are in the same folder.

## Output Formats

### CVAT (Darknet YOLO 1.1)

```
dataset_cvat.zip
├── obj.data
├── obj.names
├── train.txt
└── obj_train_data/
    ├── img001.jpg
    ├── img001.txt
    └── ...
```

Import in CVAT: **Create Task** → **Actions** → **Import dataset** → format **YOLO 1.1** → upload zip.

### Roboflow

```
dataset_roboflow.zip
├── data.yaml
└── train/
    ├── images/
    └── labels/
```

### YOLO Split

```
dataset_yolo.zip
├── data.yaml
├── images/
│   ├── train/
│   └── val/
└── labels/
    ├── train/
    └── val/
```

## Contributing

Contributions are welcome! See [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines.

Adding a new export format is ~30 lines — just write an `export_xxx()` function and add it to the `EXPORTERS` dict.

## Changelog

See [CHANGELOG.md](CHANGELOG.md) for release history.

## License

MIT
