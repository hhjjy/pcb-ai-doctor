#!/usr/bin/env python3
"""
Prepare YOLO-format dataset from PCB detection data on the feature branch.

Extracts chunk images and detection.json from git, maps absolute bbox
coordinates to chunk-local coordinates, and outputs YOLO format labels.

Usage:
    python scripts/prepare_dataset.py [--val-ratio 0.2] [--seed 42]
"""

import argparse
import json
import os
import random
import shutil
import subprocess
import sys
from pathlib import Path

# Git branch containing the source data
SOURCE_BRANCH = "origin/feature/yihua/demo-frontend-fix"

# Data paths on the feature branch (relative to repo root)
SIDES = {
    "back": {
        "detection": "scans/MMS_DEMO/back/4_detect/merged/detection.json",
        "chunks_meta": "scans/MMS_DEMO/back/4_detect/chunks_nobg/chunks_meta.json",
        "chunks_dir": "scans/MMS_DEMO/back/4_detect/chunks_nobg",
    },
    "front": {
        "detection": "scans/MMS_DEMO/front/4_detect/pro_think/merged/detection.json",
        "chunks_meta": "scans/MMS_DEMO/front/4_detect/chunks_nobg/chunks_meta.json",
        "chunks_dir": "scans/MMS_DEMO/front/4_detect/chunks_nobg",
    },
}

# Class mapping: all types -> single class 0 (component)
TYPE_TO_CLASS = {
    "ic": 0,
    "IC": 0,
    "SOT-23": 0,
    "SOT-23/Transistor": 0,
    "SOT-223": 0,
    "Module": 0,
}


def git_show(ref_path: str) -> bytes:
    """Extract file content from git ref."""
    result = subprocess.run(
        ["git", "show", f"{SOURCE_BRANCH}:{ref_path}"],
        capture_output=True,
    )
    if result.returncode != 0:
        raise RuntimeError(
            f"git show failed for {ref_path}: {result.stderr.decode()}"
        )
    return result.stdout


def git_show_json(ref_path: str) -> dict:
    """Extract and parse JSON file from git ref."""
    return json.loads(git_show(ref_path))


def extract_chunk_image(ref_path: str, dest: Path):
    """Extract a binary file (image) from git to disk."""
    data = git_show(ref_path)
    dest.write_bytes(data)


def bbox_to_yolo(
    bbox: list[int],
    chunk_offset_x: int,
    chunk_offset_y: int,
    chunk_w: int,
    chunk_h: int,
) -> tuple[float, float, float, float] | None:
    """
    Convert absolute [x1, y1, x2, y2] bbox to YOLO format
    (x_center, y_center, width, height) normalized to [0, 1]
    relative to the given chunk.

    Returns None if the bbox doesn't overlap with this chunk.
    """
    x1, y1, x2, y2 = bbox

    # Convert to chunk-local coordinates
    local_x1 = x1 - chunk_offset_x
    local_y1 = y1 - chunk_offset_y
    local_x2 = x2 - chunk_offset_x
    local_y2 = y2 - chunk_offset_y

    # Clip to chunk boundaries
    local_x1 = max(0, local_x1)
    local_y1 = max(0, local_y1)
    local_x2 = min(chunk_w, local_x2)
    local_y2 = min(chunk_h, local_y2)

    # Check if there's meaningful overlap (at least 30% of original bbox area)
    clipped_w = local_x2 - local_x1
    clipped_h = local_y2 - local_y1
    if clipped_w <= 0 or clipped_h <= 0:
        return None

    orig_w = x2 - x1
    orig_h = y2 - y1
    orig_area = orig_w * orig_h
    clipped_area = clipped_w * clipped_h
    if orig_area > 0 and clipped_area / orig_area < 0.3:
        return None

    # Convert to YOLO format (normalized center + size)
    x_center = (local_x1 + local_x2) / 2.0 / chunk_w
    y_center = (local_y1 + local_y2) / 2.0 / chunk_h
    w = clipped_w / chunk_w
    h = clipped_h / chunk_h

    return (x_center, y_center, w, h)


def process_side(
    side: str,
    config: dict,
    dataset_dir: Path,
    assignments: dict[str, str],
) -> dict:
    """Process one side (front/back), return stats."""
    print(f"\n{'='*60}")
    print(f"Processing: {side}")
    print(f"{'='*60}")

    # Load metadata
    detection = git_show_json(config["detection"])
    chunks_meta = git_show_json(config["chunks_meta"])

    components = detection["components"]
    chunks = {c["filename"]: c for c in chunks_meta["chunks"]}

    print(f"  Components: {len(components)}")
    print(f"  Chunks: {len(chunks)}")

    stats = {"images": 0, "labels": 0, "skipped_type": 0}

    # For each chunk, find overlapping components and create labels
    for chunk_info in chunks_meta["chunks"]:
        filename = chunk_info["filename"]
        ox = chunk_info["offset_x"]
        oy = chunk_info["offset_y"]
        cw = chunk_info["width"]
        ch = chunk_info["height"]

        # Determine split
        # Use side+filename as unique key for consistent assignment
        key = f"{side}_{filename}"
        split = assignments.get(key, "train")

        # Find all components that overlap with this chunk
        labels = []
        for comp in components:
            comp_type = comp["type"]
            class_id = TYPE_TO_CLASS.get(comp_type)
            if class_id is None:
                stats["skipped_type"] += 1
                continue

            yolo_box = bbox_to_yolo(comp["bbox"], ox, oy, cw, ch)
            if yolo_box is None:
                continue

            labels.append((class_id, *yolo_box))

        # Unique image name: side_chunkname
        img_name = f"{side}_{filename}"
        label_name = img_name.replace(".jpg", ".txt")

        # Extract image
        chunk_ref = f"{config['chunks_dir']}/{filename}"
        img_dest = dataset_dir / "images" / split / img_name
        extract_chunk_image(chunk_ref, img_dest)
        stats["images"] += 1

        # Write label file (even if empty — YOLO needs it for negative examples)
        label_dest = dataset_dir / "labels" / split / label_name
        with open(label_dest, "w") as f:
            for label in labels:
                f.write(f"{label[0]} {label[1]:.6f} {label[2]:.6f} {label[3]:.6f} {label[4]:.6f}\n")
                stats["labels"] += 1

        if labels:
            print(f"  {img_name} -> {split}: {len(labels)} labels")
        else:
            print(f"  {img_name} -> {split}: (negative)")

    return stats


def main():
    parser = argparse.ArgumentParser(description="Prepare YOLO dataset from PCB detection data")
    parser.add_argument("--val-ratio", type=float, default=0.2, help="Validation split ratio")
    parser.add_argument("--seed", type=int, default=42, help="Random seed")
    args = parser.parse_args()

    # Paths
    script_dir = Path(__file__).resolve().parent
    project_dir = script_dir.parent
    dataset_dir = project_dir / "dataset"

    # Clean existing dataset
    for sub in ["images/train", "images/val", "labels/train", "labels/val"]:
        d = dataset_dir / sub
        if d.exists():
            shutil.rmtree(d)
        d.mkdir(parents=True, exist_ok=True)

    # Collect all chunk filenames for split assignment
    all_keys = []
    for side, config in SIDES.items():
        chunks_meta = git_show_json(config["chunks_meta"])
        for chunk in chunks_meta["chunks"]:
            all_keys.append(f"{side}_{chunk['filename']}")

    # Randomly assign to train/val
    random.seed(args.seed)
    random.shuffle(all_keys)
    n_val = max(1, int(len(all_keys) * args.val_ratio))
    val_keys = set(all_keys[:n_val])
    assignments = {k: "val" if k in val_keys else "train" for k in all_keys}

    print(f"Total chunks: {len(all_keys)}")
    print(f"Train: {len(all_keys) - n_val}, Val: {n_val}")

    # Process each side
    total_stats = {"images": 0, "labels": 0, "skipped_type": 0}
    for side, config in SIDES.items():
        stats = process_side(side, config, dataset_dir, assignments)
        for k in total_stats:
            total_stats[k] += stats[k]

    # Summary
    print(f"\n{'='*60}")
    print("Dataset Summary")
    print(f"{'='*60}")
    print(f"  Total images: {total_stats['images']}")
    print(f"  Total labels: {total_stats['labels']}")
    if total_stats["skipped_type"] > 0:
        print(f"  Skipped (unknown type): {total_stats['skipped_type']}")

    # Count per split
    for split in ["train", "val"]:
        n_img = len(list((dataset_dir / "images" / split).glob("*.jpg")))
        n_lbl = 0
        for lbl_file in (dataset_dir / "labels" / split).glob("*.txt"):
            with open(lbl_file) as f:
                n_lbl += sum(1 for line in f if line.strip())
        print(f"  {split}: {n_img} images, {n_lbl} labels")

    print(f"\nDataset ready at: {dataset_dir}")
    print("Run training with: docker compose up")


if __name__ == "__main__":
    main()
