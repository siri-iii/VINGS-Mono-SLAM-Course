#!/usr/bin/env python3
"""Export a NeuralSim Waymo sequence into the minimal VINGS-Mono Waymo layout."""
import argparse
import pickle
import shutil
from pathlib import Path

import numpy as np


def link_or_copy(source, target, copy_files):
    if target.exists() or target.is_symlink():
        target.unlink()
    if copy_files:
        shutil.copy2(source, target)
    else:
        target.symlink_to(source.resolve())


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("processed_scene", help="NeuralSim processed segment directory")
    parser.add_argument("output_dir", help="VINGS Waymo_Scene13 directory")
    parser.add_argument("--camera", default="camera_FRONT")
    parser.add_argument("--copy", action="store_true", help="Copy images instead of creating symlinks")
    parser.add_argument("--force", action="store_true", help="Replace an existing color/pose export")
    args = parser.parse_args()

    source = Path(args.processed_scene)
    output = Path(args.output_dir)
    scenario_path = source / "scenario.pt"
    image_dir = source / "images" / args.camera
    if not scenario_path.is_file() or not image_dir.is_dir():
        raise SystemExit(f"Missing NeuralSim output: expected {scenario_path} and {image_dir}")

    color_dir, pose_dir = output / "color", output / "pose"
    if not args.force and (color_dir.exists() or pose_dir.exists()):
        raise SystemExit(f"Refusing to replace {output}; pass --force after verifying the segment mapping")
    shutil.rmtree(color_dir, ignore_errors=True)
    shutil.rmtree(pose_dir, ignore_errors=True)
    color_dir.mkdir(parents=True)
    pose_dir.mkdir(parents=True)

    with scenario_path.open("rb") as handle:
        scenario = pickle.load(handle)
    try:
        poses = np.asarray(scenario["observers"][args.camera]["data"]["c2w"], dtype=np.float64)
    except KeyError as exc:
        raise SystemExit(f"Camera {args.camera!r} missing from {scenario_path}: {exc}") from exc
    images = sorted(image_dir.glob("*.jpg"))
    if len(images) != len(poses):
        raise SystemExit(f"Image/pose count mismatch: {len(images)} images vs {len(poses)} poses")

    for frame, (image_path, pose) in enumerate(zip(images, poses)):
        link_or_copy(image_path, color_dir / f"{frame:05d}.jpg", args.copy)
        np.savetxt(pose_dir / f"{frame:05d}.txt", pose.reshape(4, 4))
    (output / "SOURCE_SEGMENT.txt").write_text(source.name + "\n", encoding="utf-8")
    print(f"Exported {len(images)} {args.camera} frames from {source.name} to {output}")


if __name__ == "__main__":
    main()
