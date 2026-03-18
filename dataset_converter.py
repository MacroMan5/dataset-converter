#!/usr/bin/env python3
"""
Dataset Converter — Convert YOLO datasets for annotation platforms.

Converts image/label datasets into ready-to-import archives for:
- CVAT (Darknet YOLO 1.1 format)
- Roboflow (YOLO folder upload)
- YOLO Split (standard train/val with data.yaml)

Supports any YOLO-format dataset with any number of classes.
Auto-detects class IDs from label files and lets you name them.

No dependencies required — uses only Python standard library + tkinter.

Usage:
    python dataset_converter.py                  # Launch GUI
    python dataset_converter.py --cli -i dataset/ -f cvat -c head player
"""

from __future__ import annotations

import argparse
import random
import zipfile
from pathlib import Path
from typing import Optional

IMAGE_EXTENSIONS = ("*.jpg", "*.jpeg", "*.png", "*.bmp", "*.webp")


# ── Dataset scanning ─────────────────────────────────────────────────


def find_image_label_pairs(dataset_dir: Path) -> list[tuple[Path, Optional[Path]]]:
    """Find matching image/label pairs from a dataset directory."""
    img_dir = dataset_dir / "images" if (dataset_dir / "images").exists() else dataset_dir
    lbl_dir = dataset_dir / "labels" if (dataset_dir / "labels").exists() else dataset_dir

    pairs = []
    for ext in IMAGE_EXTENSIONS:
        for img in sorted(img_dir.glob(ext)):
            lbl = lbl_dir / f"{img.stem}.txt"
            pairs.append((img, lbl if lbl.exists() else None))

    return pairs


def scan_class_ids(dataset_dir: Path) -> list[int]:
    """Scan all label files and return sorted unique class IDs found."""
    lbl_dir = dataset_dir / "labels" if (dataset_dir / "labels").exists() else dataset_dir

    class_ids: set[int] = set()
    for txt in lbl_dir.glob("*.txt"):
        try:
            for line in txt.read_text().strip().splitlines():
                parts = line.strip().split()
                if len(parts) >= 5:
                    class_ids.add(int(parts[0]))
        except (ValueError, OSError):
            continue

    return sorted(class_ids)


# ── Exporters ─────────────────────────────────────────────────────────


def export_cvat(
    dataset_dir: Path, output_path: Path, classes: list[str],
    include_labels: bool = True, **_
) -> int:
    """
    Export as CVAT-compatible Darknet YOLO 1.1 ZIP.

    Structure:
        obj.data
        obj.names
        train.txt
        obj_train_data/
            img001.jpg
            img001.txt
    """
    pairs = find_image_label_pairs(dataset_dir)
    if not pairs:
        raise FileNotFoundError(f"No images found in {dataset_dir}")

    with zipfile.ZipFile(output_path, "w", zipfile.ZIP_DEFLATED) as zf:
        zf.writestr("obj.names", "\n".join(classes) + "\n")

        train_lines = []
        for img, lbl in pairs:
            arc_name = f"obj_train_data/{img.name}"
            train_lines.append(arc_name)
            zf.write(img, arc_name)
            if include_labels and lbl:
                zf.write(lbl, f"obj_train_data/{img.stem}.txt")

        zf.writestr("train.txt", "\n".join(train_lines) + "\n")
        zf.writestr("obj.data", (
            f"classes = {len(classes)}\n"
            f"names = obj.names\n"
            f"train = train.txt\n"
            f"backup = backup/\n"
        ))

    return len(pairs)


def export_roboflow(
    dataset_dir: Path, output_path: Path, classes: list[str],
    include_labels: bool = True, **_
) -> int:
    """
    Export as Roboflow-compatible YOLO ZIP.

    Structure:
        train/images/  train/labels/  data.yaml
    """
    pairs = find_image_label_pairs(dataset_dir)
    if not pairs:
        raise FileNotFoundError(f"No images found in {dataset_dir}")

    with zipfile.ZipFile(output_path, "w", zipfile.ZIP_DEFLATED) as zf:
        for img, lbl in pairs:
            zf.write(img, f"train/images/{img.name}")
            if include_labels and lbl:
                zf.write(lbl, f"train/labels/{img.stem}.txt")

        zf.writestr("data.yaml", (
            f"train: train/images\n"
            f"val: train/images\n"
            f"nc: {len(classes)}\n"
            f"names: {classes}\n"
        ))

    return len(pairs)


def export_yolo_split(
    dataset_dir: Path, output_path: Path, classes: list[str],
    include_labels: bool = True, val_ratio: float = 0.2, **_
) -> tuple[int, int, int]:
    """
    Export as standard YOLO with train/val split.

    Structure:
        images/train/  images/val/  labels/train/  labels/val/  data.yaml
    """
    pairs = find_image_label_pairs(dataset_dir)
    if not pairs:
        raise FileNotFoundError(f"No images found in {dataset_dir}")

    shuffled = list(pairs)
    random.shuffle(shuffled)
    split_idx = max(1, int(len(shuffled) * (1 - val_ratio)))
    train_pairs = shuffled[:split_idx]
    val_pairs = shuffled[split_idx:]

    with zipfile.ZipFile(output_path, "w", zipfile.ZIP_DEFLATED) as zf:
        for split_name, split_pairs in [("train", train_pairs), ("val", val_pairs)]:
            for img, lbl in split_pairs:
                zf.write(img, f"images/{split_name}/{img.name}")
                if include_labels and lbl:
                    zf.write(lbl, f"labels/{split_name}/{img.stem}.txt")

        zf.writestr("data.yaml", (
            f"train: images/train\n"
            f"val: images/val\n"
            f"nc: {len(classes)}\n"
            f"names: {classes}\n"
        ))

    return len(pairs), len(train_pairs), len(val_pairs)


EXPORTERS = {
    "cvat": ("CVAT (Darknet YOLO 1.1)", export_cvat),
    "roboflow": ("Roboflow (YOLO folder)", export_roboflow),
    "yolo": ("YOLO Split (train/val)", export_yolo_split),
}


# ── GUI ───────────────────────────────────────────────────────────────


def launch_gui():
    import tkinter as tk
    from tkinter import ttk, filedialog, messagebox

    root = tk.Tk()
    root.title("Dataset Converter")
    root.geometry("560x500")
    root.resizable(False, False)

    style = ttk.Style()
    style.configure("Header.TLabel", font=("Segoe UI", 12, "bold"))
    style.configure("Sub.TLabel", font=("Segoe UI", 9), foreground="gray")
    style.configure("Big.TButton", font=("Segoe UI", 10, "bold"), padding=8)

    # State
    input_var = tk.StringVar()
    output_var = tk.StringVar()
    format_var = tk.StringVar(value="cvat")
    labels_var = tk.BooleanVar(value=True)
    status_var = tk.StringVar(value="Select a dataset folder to begin.")
    class_entries: list[tuple[tk.StringVar, int]] = []  # (name_var, class_id)

    frame = ttk.Frame(root, padding=16)
    frame.pack(fill="both", expand=True)

    # Header
    ttk.Label(frame, text="Dataset Converter", style="Header.TLabel").grid(
        row=0, column=0, columnspan=3, sticky="w"
    )
    ttk.Label(frame, text="YOLO datasets → CVAT / Roboflow / YOLO split", style="Sub.TLabel").grid(
        row=1, column=0, columnspan=3, sticky="w", pady=(0, 10)
    )

    # Input
    ttk.Label(frame, text="Input folder:").grid(row=2, column=0, sticky="w")
    ttk.Entry(frame, textvariable=input_var, width=42).grid(row=2, column=1, sticky="ew", padx=4)
    ttk.Button(frame, text="Browse", command=lambda: browse_input()).grid(row=2, column=2)

    # Classes frame (dynamic)
    classes_label = ttk.Label(frame, text="Classes:")
    classes_label.grid(row=3, column=0, sticky="nw", pady=(8, 0))

    classes_container = ttk.Frame(frame)
    classes_container.grid(row=3, column=1, columnspan=2, sticky="ew", padx=4, pady=(8, 0))

    classes_hint = ttk.Label(classes_container, text="Load a dataset to detect classes.", foreground="gray")
    classes_hint.pack(anchor="w")

    # Output
    ttk.Label(frame, text="Output file:").grid(row=4, column=0, sticky="w", pady=(8, 0))
    ttk.Entry(frame, textvariable=output_var, width=42).grid(row=4, column=1, sticky="ew", padx=4, pady=(8, 0))
    ttk.Button(frame, text="Browse", command=lambda: browse_output()).grid(row=4, column=2, pady=(8, 0))

    # Format
    ttk.Label(frame, text="Format:").grid(row=5, column=0, sticky="nw", pady=(8, 0))
    fmt_frame = ttk.Frame(frame)
    fmt_frame.grid(row=5, column=1, columnspan=2, sticky="w", padx=4, pady=(8, 0))
    for key, (label, _) in EXPORTERS.items():
        ttk.Radiobutton(fmt_frame, text=label, variable=format_var, value=key,
                        command=lambda: update_output_name()).pack(anchor="w")

    # Include labels
    ttk.Checkbutton(frame, text="Include existing annotations", variable=labels_var).grid(
        row=6, column=1, sticky="w", padx=4, pady=(6, 0)
    )

    # Convert
    ttk.Button(frame, text="Convert", style="Big.TButton", command=lambda: do_convert()).grid(
        row=7, column=0, columnspan=3, sticky="ew", pady=(14, 4)
    )

    # Status
    ttk.Label(frame, textvariable=status_var, foreground="gray", wraplength=500).grid(
        row=8, column=0, columnspan=3, sticky="w"
    )

    frame.columnconfigure(1, weight=1)

    # ── Handlers ──

    def browse_input():
        d = filedialog.askdirectory(title="Select dataset folder (with images/ and labels/)")
        if not d:
            return
        input_var.set(d)
        load_classes(Path(d))
        update_output_name()

    def load_classes(dataset_dir: Path):
        nonlocal class_entries

        # Clear old
        for widget in classes_container.winfo_children():
            widget.destroy()
        class_entries.clear()

        # Count images
        pairs = find_image_label_pairs(dataset_dir)
        img_count = len(pairs)
        lbl_count = sum(1 for _, l in pairs if l is not None)

        # Scan class IDs
        ids = scan_class_ids(dataset_dir)

        if not ids:
            ttk.Label(classes_container, text=f"{img_count} images, no labels found. Classes will be empty.",
                      foreground="orange").pack(anchor="w")
            status_var.set(f"Found {img_count} images, 0 labels.")
            return

        ttk.Label(classes_container,
                  text=f"Found {len(ids)} class(es) in {lbl_count} labels. Name each one:",
                  foreground="gray").pack(anchor="w", pady=(0, 4))

        for cid in ids:
            row_frame = ttk.Frame(classes_container)
            row_frame.pack(fill="x", pady=1)

            ttk.Label(row_frame, text=f"ID {cid}:", width=6).pack(side="left")
            name_var = tk.StringVar(value=f"class_{cid}")
            ttk.Entry(row_frame, textvariable=name_var, width=30).pack(side="left", padx=4)
            class_entries.append((name_var, cid))

        status_var.set(f"Found {img_count} images, {lbl_count} labels, {len(ids)} classes.")

    def browse_output():
        f = filedialog.asksaveasfilename(
            title="Save as",
            defaultextension=".zip",
            filetypes=[("ZIP archive", "*.zip")],
            initialfile=output_var.get() or "dataset_export.zip",
        )
        if f:
            output_var.set(f)

    def update_output_name():
        inp = input_var.get()
        fmt = format_var.get()
        if inp:
            name = Path(inp).name
            output_var.set(f"{name}_{fmt}.zip")

    def get_classes() -> list[str]:
        """Build ordered class list from UI entries."""
        if not class_entries:
            return []
        max_id = max(cid for _, cid in class_entries)
        classes = [f"class_{i}" for i in range(max_id + 1)]
        for name_var, cid in class_entries:
            classes[cid] = name_var.get().strip() or f"class_{cid}"
        return classes

    def do_convert():
        inp = input_var.get().strip()
        out = output_var.get().strip()
        fmt = format_var.get()
        classes = get_classes()

        if not inp or not Path(inp).is_dir():
            messagebox.showerror("Error", "Select a valid input folder.")
            return
        if not out:
            messagebox.showerror("Error", "Specify an output file.")
            return

        output_path = Path(out) if Path(out).is_absolute() else Path(inp).parent / out

        try:
            _, exporter = EXPORTERS[fmt]
            result = exporter(Path(inp), output_path, classes, include_labels=labels_var.get())

            if isinstance(result, tuple):
                total, train, val = result
                msg = f"Exported {total} images ({train} train / {val} val)"
            else:
                msg = f"Exported {result} images"

            size_mb = output_path.stat().st_size / 1024 / 1024
            status_var.set(f"{msg} → {output_path.name} ({size_mb:.1f} MB)")
            messagebox.showinfo("Done", (
                f"{msg}\n"
                f"Classes: {classes}\n\n"
                f"Saved to:\n{output_path}"
            ))

        except Exception as e:
            messagebox.showerror("Error", str(e))
            status_var.set(f"Error: {e}")

    root.mainloop()


# ── CLI ───────────────────────────────────────────────────────────────


def cli_main():
    parser = argparse.ArgumentParser(
        description="Universal YOLO dataset converter for annotation platforms."
    )
    parser.add_argument("--cli", action="store_true", help="Run in CLI mode (no GUI)")
    parser.add_argument("-i", "--input", type=Path, help="Input dataset directory")
    parser.add_argument("-o", "--output", type=Path, help="Output ZIP path")
    parser.add_argument(
        "-f", "--format", choices=EXPORTERS.keys(), default="cvat",
        help="Output format (default: cvat)"
    )
    parser.add_argument(
        "-c", "--classes", nargs="+",
        help="Class names in order (e.g. -c dog cat bird). Auto-detected from labels if omitted."
    )
    parser.add_argument("--no-labels", action="store_true", help="Exclude existing annotations")
    parser.add_argument("--val-ratio", type=float, default=0.2, help="Validation split ratio (default: 0.2)")

    args = parser.parse_args()

    if not args.cli:
        launch_gui()
        return

    if not args.input:
        parser.error("--input is required in CLI mode")

    # Auto-detect classes if not provided
    if not args.classes:
        ids = scan_class_ids(args.input)
        if ids:
            args.classes = [f"class_{i}" for i in range(max(ids) + 1)]
            print(f"Auto-detected {len(ids)} class IDs: {ids}")
            print(f"Using default names: {args.classes}")
            print("Tip: use -c to name them (e.g. -c head player)\n")
        else:
            args.classes = []
            print("No class IDs found in labels.\n")

    if not args.output:
        args.output = Path(f"{args.input.name}_{args.format}.zip")

    label, exporter = EXPORTERS[args.format]
    print(f"Format:  {label}")
    print(f"Input:   {args.input}")
    print(f"Output:  {args.output}")
    print(f"Classes: {args.classes}")
    print()

    result = exporter(
        args.input, args.output, args.classes,
        include_labels=not args.no_labels, val_ratio=args.val_ratio
    )

    if isinstance(result, tuple):
        total, train, val = result
        print(f"Exported {total} images ({train} train / {val} val)")
    else:
        print(f"Exported {result} images")

    size_mb = args.output.stat().st_size / 1024 / 1024
    print(f"Saved: {args.output} ({size_mb:.1f} MB)")


if __name__ == "__main__":
    cli_main()
