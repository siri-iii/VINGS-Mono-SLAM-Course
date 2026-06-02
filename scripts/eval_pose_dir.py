#!/usr/bin/env python3
"""Evaluate droid_c2w keyframes against a directory of 4x4 ground-truth poses."""
import argparse
import glob
import json
import os

import numpy as np


def load_pose_dir(path):
    files = sorted(glob.glob(os.path.join(path, "*.txt")), key=lambda p: float(os.path.splitext(os.path.basename(p))[0]))
    indices = np.array([int(float(os.path.splitext(os.path.basename(p))[0])) for p in files], dtype=np.int64)
    poses = np.array([np.loadtxt(p).reshape(4, 4) for p in files], dtype=np.float64)
    return indices, poses


def align_sim3(src, dst):
    src_mean, dst_mean = src.mean(0), dst.mean(0)
    x, y = src - src_mean, dst - dst_mean
    cov = (y.T @ x) / len(src)
    u, singular, vt = np.linalg.svd(cov)
    sign = np.eye(3)
    sign[2, 2] = np.sign(np.linalg.det(u @ vt))
    rot = u @ sign @ vt
    scale = np.trace(np.diag(singular) @ sign) / (np.sum(x * x) / len(src))
    trans = dst_mean - scale * rot @ src_mean
    return scale, rot, trans


def evaluate(result_dir, gt_dir):
    pred_idx, pred = load_pose_dir(os.path.join(result_dir, "droid_c2w"))
    gt_idx, gt = load_pose_dir(gt_dir)
    if len(pred) == 0 or len(gt) == 0:
        raise ValueError("Both prediction and GT pose directories must contain .txt poses")
    gt_by_idx = {idx: pose for idx, pose in zip(gt_idx.tolist(), gt)}
    pairs = [(idx, pose, gt_by_idx[idx]) for idx, pose in zip(pred_idx.tolist(), pred) if idx in gt_by_idx]
    if not pairs:
        raise ValueError("Prediction and GT directories have no overlapping frame IDs")
    indices = np.array([item[0] for item in pairs], dtype=np.int64)
    pred_xyz = np.array([item[1][:3, 3] for item in pairs], dtype=np.float64)
    gt_xyz = np.array([item[2][:3, 3] for item in pairs], dtype=np.float64)
    scale, rot, trans = align_sim3(pred_xyz, gt_xyz)
    aligned = (scale * (rot @ pred_xyz.T)).T + trans
    errors = np.linalg.norm(aligned - gt_xyz, axis=1)
    return {
        "prediction_frames": len(pred), "gt_frames": len(gt), "matched_frames": len(pairs),
        "frame_start": int(indices[0]), "frame_end": int(indices[-1]),
        "ate_rmse_m": float(np.sqrt(np.mean(errors ** 2))),
        "ate_median_m": float(np.median(errors)), "sim3_scale": float(scale),
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("result_dir")
    parser.add_argument("gt_pose_dir")
    parser.add_argument("--output")
    args = parser.parse_args()
    result = evaluate(args.result_dir, args.gt_pose_dir)
    output = args.output or os.path.join(args.result_dir, "ate_result.json")
    os.makedirs(os.path.dirname(output) or ".", exist_ok=True)
    with open(output, "w", encoding="utf-8") as handle:
        json.dump(result, handle, indent=2, sort_keys=True)
        handle.write("\n")
    print("[ATE] " + json.dumps(result, sort_keys=True))
    print(f"Saved to {output}")


if __name__ == "__main__":
    main()
