"""
A2: KITTI-07 trajectory comparison.
A3: mono-only vs mono+IMU metric bar chart.

Usage:
  python scripts/plot_traj.py --vo_dir <kitti07_vo_result> --vio_dir <kitti07_vio_result>
"""
import argparse
import glob
import os

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

from eval_kitti import align_sim3, apply_sim3, load_gt_poses, load_result_traj

MEDIA = "/root/autodl-tmp/VINGS-Mono-SLAM-Course/media/figures"
os.makedirs(MEDIA, exist_ok=True)


def align_xyz(pred_xyz, gt_xyz):
    scale, rot, trans = align_sim3(pred_xyz, gt_xyz)
    return (scale * (rot @ pred_xyz.T)).T + trans


def ate(pred_xyz, gt_xyz):
    aligned = align_xyz(pred_xyz, gt_xyz)
    return float(np.sqrt(np.mean(np.linalg.norm(aligned - gt_xyz, axis=1) ** 2)))


def read_eval(result_dir):
    path = os.path.join(result_dir, "ate_trel_result.txt")
    if not os.path.exists(path):
        return {}
    values = {}
    with open(path, encoding="utf-8") as handle:
        for line in handle:
            if "=" not in line:
                continue
            key, value = line.strip().split("=", 1)
            try:
                values[key] = float(value)
            except ValueError:
                pass
    return values


def plot_traj(vo_dir, vio_dir=None, seq="07"):
    gt_all = load_gt_poses(seq)
    fig, ax = plt.subplots(1, 1, figsize=(9, 6))
    ax.plot(gt_all[:, 0, 3], gt_all[:, 2, 3], "k-", lw=2, label="Ground Truth")

    vo_idx, vo_poses, _ = load_result_traj(vo_dir)
    vo_gt = gt_all[vo_idx]
    vo_aligned = align_xyz(vo_poses[:, :3, 3], vo_gt[:, :3, 3])
    ax.plot(vo_aligned[:, 0], vo_aligned[:, 2], "b-", lw=1.5,
            label=f"VINGS-Mono VO (ATE={ate(vo_poses[:, :3, 3], vo_gt[:, :3, 3]):.2f}m)")

    if vio_dir and os.path.exists(vio_dir):
        vio_idx, vio_poses, _ = load_result_traj(vio_dir)
        vio_gt = gt_all[vio_idx]
        vio_aligned = align_xyz(vio_poses[:, :3, 3], vio_gt[:, :3, 3])
        ax.plot(vio_aligned[:, 0], vio_aligned[:, 2], "r-", lw=1.5,
                label=f"VINGS-Mono VIO (ATE={ate(vio_poses[:, :3, 3], vio_gt[:, :3, 3]):.2f}m)")

    ax.set_xlabel("X (m)")
    ax.set_ylabel("Z (m)")
    ax.set_title(f"KITTI-{seq} Timestamp-Matched Trajectory Comparison")
    ax.legend()
    ax.set_aspect("equal")
    ax.grid(True, alpha=0.3)
    plt.tight_layout()
    out = os.path.join(MEDIA, "traj_kitti07_compare.png")
    plt.savefig(out, dpi=150, bbox_inches="tight")
    plt.close()
    print(f"Saved A2: {out}")


def plot_bar(vo_dir, vio_dir=None):
    vo = read_eval(vo_dir) if vo_dir else {}
    vio = read_eval(vio_dir) if vio_dir else {}
    labels = ["ATE (m)", "trel (%)", "rrel (deg/100m)"]
    keys = ["ATE_RMSE_m", "trel_pct", "rrel_deg_per_100m"]
    x = np.arange(len(labels))
    width = 0.3
    bars1 = [vo.get(key, 0.0) for key in keys]
    bars2 = [vio.get(key, 0.0) for key in keys]

    fig, ax = plt.subplots(figsize=(8, 5))
    ax.bar(x - width / 2, bars1, width, label="Mono-only (VO)", color="#4e9af1", alpha=0.85)
    ax.bar(x + width / 2, bars2, width, label="Mono+IMU (VIO)", color="#f17a4e", alpha=0.85)
    ymax = max(bars1 + bars2 + [1.0])
    for i, (v1, v2) in enumerate(zip(bars1, bars2)):
        if v1 > 0:
            ax.text(i - width / 2, v1 + 0.015 * ymax, f"{v1:.2f}", ha="center", fontsize=8)
        if v2 > 0:
            ax.text(i + width / 2, v2 + 0.015 * ymax, f"{v2:.2f}", ha="center", fontsize=8)
    ax.set_xticks(x)
    ax.set_xticklabels(labels)
    ax.set_title("KITTI-07: Mono-only vs Mono+IMU (timestamp matched)")
    ax.legend()
    ax.grid(axis="y", alpha=0.3)
    plt.tight_layout()
    out = os.path.join(MEDIA, "vio_vs_vo_bar.png")
    plt.savefig(out, dpi=150, bbox_inches="tight")
    plt.close()
    print(f"Saved A3: {out}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--vo_dir", default=None)
    parser.add_argument("--vio_dir", default=None)
    parser.add_argument("--seq", default="07")
    args = parser.parse_args()

    if args.vo_dir is None:
        dirs = sorted(glob.glob("/root/autodl-tmp/VINGS-Mono-SLAM-Course/results/frontend/kitti07_vo/*/"))
        if dirs:
            args.vo_dir = dirs[-1]
    if args.vio_dir is None:
        dirs = sorted(glob.glob("/root/autodl-tmp/VINGS-Mono-SLAM-Course/results/frontend/kitti07_vio/*/"))
        if dirs:
            args.vio_dir = dirs[-1]

    print(f"VO  dir: {args.vo_dir}")
    print(f"VIO dir: {args.vio_dir}")
    if args.vo_dir:
        plot_traj(args.vo_dir, args.vio_dir, args.seq)
        plot_bar(args.vo_dir, args.vio_dir)
    else:
        print("No result dir found. Run experiments first.")
