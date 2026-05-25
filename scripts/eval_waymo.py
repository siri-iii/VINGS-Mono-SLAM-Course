"""Evaluate a Waymo frontend result against `pose/*.txt` in the staged Scene01 folder."""
import argparse
import glob
import os

import numpy as np


def load_poses_from_dir(path):
    files = sorted(glob.glob(os.path.join(path, "*.txt")), key=lambda p: float(os.path.splitext(os.path.basename(p))[0]))
    if not files:
        return np.empty((0,), dtype=np.int64), np.empty((0, 4, 4), dtype=np.float64)
    indices = np.array([int(float(os.path.splitext(os.path.basename(path))[0])) for path in files], dtype=np.int64)
    poses = np.array([np.loadtxt(path).reshape(4, 4) for path in files], dtype=np.float64)
    return indices, poses


def align_sim3(src, dst):
    mu_s, mu_d = src.mean(0), dst.mean(0)
    x, y = src - mu_s, dst - mu_d
    cov = (y.T @ x) / len(src)
    u, singular, vt = np.linalg.svd(cov)
    sign = np.eye(3)
    sign[2, 2] = np.sign(np.linalg.det(u @ vt))
    rot = u @ sign @ vt
    scale = np.trace(np.diag(singular) @ sign) / (np.sum(x * x) / len(src))
    trans = mu_d - scale * rot @ mu_s
    return scale, rot, trans


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("result_dir")
    parser.add_argument("--waymo_root", default="/root/autodl-tmp/data/waymo/Scene01")
    args = parser.parse_args()

    pred_idx, pred = load_poses_from_dir(os.path.join(args.result_dir, "droid_c2w"))
    gt_idx, gt = load_poses_from_dir(os.path.join(args.waymo_root, "pose"))
    if len(pred) == 0:
        raise SystemExit(f"No predictions found in {args.result_dir}/droid_c2w")
    if len(gt) == 0:
        raise SystemExit(f"No Waymo GT poses found in {args.waymo_root}/pose")

    gt_by_idx = {idx: pose for idx, pose in zip(gt_idx.tolist(), gt)}
    pairs = [(idx, pose, gt_by_idx[idx]) for idx, pose in zip(pred_idx.tolist(), pred) if idx in gt_by_idx]
    if not pairs:
        raise SystemExit("No prediction/GT frame IDs overlap")
    indices = np.array([item[0] for item in pairs], dtype=np.int64)
    pred_matched = np.array([item[1] for item in pairs], dtype=np.float64)
    gt_matched = np.array([item[2] for item in pairs], dtype=np.float64)

    scale, rot, trans = align_sim3(pred_matched[:, :3, 3], gt_matched[:, :3, 3])
    aligned = (scale * (rot @ pred_matched[:, :3, 3].T)).T + trans
    ate = float(np.sqrt(np.mean(np.linalg.norm(aligned - gt_matched[:, :3, 3], axis=1) ** 2)))

    print(f"Pred {len(pred)} / GT {len(gt)} / Matched {len(pairs)}")
    print(f"Frame range: {indices[0]}..{indices[-1]}")
    print(f"ATE RMSE: {ate:.6f} m")
    out = os.path.join(args.result_dir, "ate_result.txt")
    with open(out, "w", encoding="utf-8") as handle:
        handle.write(f"matched_frames={len(pairs)}\n")
        handle.write(f"frame_start={int(indices[0])}\n")
        handle.write(f"frame_end={int(indices[-1])}\n")
        handle.write(f"ATE_RMSE_m={ate:.6f}\n")
        handle.write(f"sim3_scale={scale:.6f}\n")
    print(f"Saved to {out}")


if __name__ == "__main__":
    main()
