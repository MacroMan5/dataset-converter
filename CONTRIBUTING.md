# Contributing to Dataset Converter

Thanks for your interest in contributing! This project is intentionally simple — one file, zero dependencies — and we'd like to keep it that way.

## Getting Started

```bash
git clone https://github.com/MacroMan5/dataset-converter.git
cd dataset-converter
pip install -e .
```

The entire codebase is in `src/dataset_converter/__init__.py`.

## How to Contribute

### Reporting Bugs

Open an [issue](https://github.com/MacroMan5/dataset-converter/issues) with:

- What you did (command or GUI steps)
- What you expected
- What happened instead
- Your Python version (`python --version`)
- Your OS

### Suggesting Features

Open an issue with the `enhancement` label. Good candidates:

- New export formats (Label Studio, VGG VIA, etc.)
- New input formats
- GUI improvements

### Submitting Code

1. Fork the repo
2. Create a branch (`git checkout -b feature/my-feature`)
3. Make your changes
4. Test manually with both GUI and CLI
5. Submit a pull request

## Guidelines

### Keep It Simple

- **Zero dependencies.** Don't add `pip install` requirements. The tool uses only Python stdlib + tkinter.
- **One file.** All logic stays in `src/dataset_converter/__init__.py`. Don't split into multiple modules unless absolutely necessary.
- **No over-engineering.** A new exporter is ~30 lines. Keep it that way.

### Adding a New Export Format

1. Write an `export_xxx()` function following the same signature as existing exporters
2. Add it to the `EXPORTERS` dict
3. That's it — the GUI and CLI pick it up automatically

```python
def export_labelstudio(
    dataset_dir: Path, output_path: Path, classes: list[str],
    include_labels: bool = True, **_
) -> int:
    # your export logic here
    return image_count

EXPORTERS = {
    ...
    "labelstudio": ("Label Studio (JSON)", export_labelstudio),
}
```

### Code Style

- Follow existing patterns in the file
- Use type hints
- Keep functions short and focused
- No external formatting tools required — just be consistent

### Commit Messages

- Keep them short and descriptive
- Use imperative mood ("Add X" not "Added X")

## Testing

There's no automated test suite (yet). Before submitting a PR, verify:

1. **CLI mode** works: `dataset-converter --cli -i <test_dataset> -f <your_format>`
2. **GUI mode** launches and converts: `dataset-converter`
3. **The output ZIP** is valid for the target platform (try importing it)
4. **Auto-detection** works when `-c` is not provided

## License

By contributing, you agree that your contributions will be licensed under the MIT License.
