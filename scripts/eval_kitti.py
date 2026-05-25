"""
Evaluate VINGS-Mono frontend trajectories on KITTI odometry.

The frontend writes keyframe poses as `<camera_timestamp>.txt`.  Evaluation must
therefore match each prediction to the KITTI camera timestamp instead of pairing
prediction row N with GT row N.
"""
import argparse
import glob
import os

import numpy as np

GT_DIR = "/root/autodl-tmp/data/kitti_gt/dataset/poses"
CAMSTAMP = "/root/autodl-tmp/data/kitti_raw/2011_09_30/2011_09_30_drive_0027_sync/metadata/camstamp.txt"


def load_gt_poses(seq="07"):
    data = np.loadtxt(os.path.join(GT_DIR, f"{seq}.txt"))
    poses = np.zeros((data.shape[0], 4, 4), dtype=np.float64)
    poses[:, :3, :] = data.reshape(-1, 3, 4)
    poses[:, 3, 3] = 1.0
    return poses


def load_camstamp_index():
    data = np.loadtxt(CAMSTAMP, dtype=str)
    return {round(float(row[0]), 6): idx for idx, row in enumerate(data)}


def load_result_traj(result_dir):
    c2w_dir = os.path.join(result_dir, "droid_c2w")
    files = glob.glob(os.path.join(c2w_dir, "*.txt"))
    timestamp_to_idx = load_camstamp_index()
    matched = []
    unmatched = []
    for path in files:
        timestamp = round(float(os.path.splitext(os.path.basename(path))[0]), 6)
        gt_idx = timestamp_to_idx.get(timestamp)
        if gt_idx is None:
            unmatched.append(path)
            continue
        matched.append((gt_idx, timestamp, np.loadtxt(path).reshape(4, 4)))
    matched.sort(key=lambda item: item[0])
    if not matched:
        return np.empty((0,), dtype=np.int64), np.empty((0, 4, 4)), unmatched
    indices = np.array([item[0] for item in matched], dtype=np.int64)
    poses = np.array([item[2] for item in matched], dtype=np.float64)
    return indices, poses, unmatched


def align_sim3(src, dst):
    mu_s, mu_d = src.mean(0), dst.mean(0)
    x, y = src - mu_s, dst - mu_d
    cov = (y.T @ x) / len(src)
    u, singular, vt = np.linalg.svd(cov)
    sign = np.eye(3)
    sign[2, 2] = np.sign(np.linalg.det(u @ vt))
    rot = u @ sign @ vt
    var = np.sum(x * x) / len(src)
    scale = np.trace(np.diag(singular) @ sign) / var
    trans = mu_d - scale * rot @ mu_s
    return scale, rot, trans


def apply_sim3(poses, scale, rot, trans):
    aligned = poses.copy()
    aligned[:, :3, :3] = rot @ aligned[:, :3, :3]
    aligned[:, :3, 3] = (scale * (rot @ aligned[:, :3, 3].T)).T + trans
    return aligned


def compute_ate(pred_xyz, gt_xyz):
    scale, rot, trans = align_sim3(pred_xyz, gt_xyz)
    aligned = (scale * (rot @ pred_xyz.T)).T + trans
    err = np.linalg.norm(aligned - gt_xyz, axis=1)
    return float(np.sqrt(np.mean(err ** 2))), scale


def kitti_seq_errors(poses_gt, poses_est, lengths=(100, 200, 300, 400, 500, 600, 700, 800)):
    n = min(len(poses_gt), len(poses_est))
    poses_gt, poses_est = poses_gt[:n], poses_est[:n]
    path_len = np.zeros(n, dtype=np.float64)
    for i in range(1, n):
        path_len[i] = path_len[i - 1] + np.linalg.norm(poses_gt[i, :3, 3] - poses_gt[i - 1, :3, 3])

    def last_frame(start, length):
        for i in range(start, n):
            if path_len[i] - path_len[start] >= length:
                return i
        return -1

    t_errs, r_errs = [], []
    for start in range(0, n, max(1, n // 50)):
        for length in lengths:
            end = last_frame(start, length)
            if end < 0:
                continue
            delta_gt = np.linalg.inv(poses_gt[start]) @ poses_gt[end]
            delta_est = np.linalg.inv(poses_est[start]) @ poses_est[end]
            err = np.linalg.inv(delta_gt) @ delta_est
            seg = path_len[end] - path_len[start]
            t_errs.append(np.linalg.norm(err[:3, 3]) / seg * 100)
            r_errs.append(np.degrees(np.arccos(np.clip((np.trace(err[:3, :3]) - 1) / 2, -1, 1))) / seg * 100)
    return (
        float(np.mean(t_errs)) if t_errs else float("nan"),
        float(np.mean(r_errs)) if r_errs else float("nan"),
        len(t_errs),
    )


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("result_dir")
    parser.add_argument("--seq", default="07")
    parser.add_argument("--no_scale_align", action="store_true", help="Do not Sim(3)-align poses before KITTI relative errors")
    args = parser.parse_args()

    gt_all = load_gt_poses(args.seq)
    gt_indices, pred, unmatched = load_result_traj(args.result_dir)
    if len(pred) == 0:
        raise SystemExit(f"No timestamp-matched predictions found in {args.result_dir}/droid_c2w")
    gt = gt_all[gt_indices]

    ate, scale = compute_ate(pred[:, :3, 3], gt[:, :3, 3])
    pred_for_rel = pred
    if not args.no_scale_align:
        scale_rel, rot_rel, trans_rel = align_sim3(pred[:, :3, 3], gt[:, :3, 3])
        pred_for_rel = apply_sim3(pred, scale_rel, rot_rel, trans_rel)
    trel, rrel, segments = kitti_seq_errors(gt, pred_for_rel)

    print(f"Pred {len(pred)} / GT {len(gt_all)} / Matched {len(gt)}")
    print(f"GT index range: {gt_indices[0]}..{gt_indices[-1]}")
    if unmatched:
        print(f"Unmatched prediction files: {len(unmatched)}")
    print(f"\n{'=' * 38}\n  KITTI-{args.seq} Results\n{'=' * 38}")
    print(f"  ATE  RMSE : {ate:.4f} m")
    print(f"  Sim3 scale: {scale:.6f}")
    print(f"  trel      : {trel:.4f} %   (paper target <=1.5%)")
    print(f"  rrel      : {rrel:.4f} deg/100m")
    print(f"  segments  : {segments}\n{'=' * 38}")

    out = os.path.join(args.result_dir, "ate_trel_result.txt")
    with open(out, "w", encoding="utf-8") as handle:
        handle.write(f"matched_frames={len(pred)}\n")
        handle.write(f"gt_start_idx={int(gt_indices[0])}\n")
        handle.write(f"gt_end_idx={int(gt_indices[-1])}\n")
        handle.write(f"ATE_RMSE_m={ate:.6f}\n")
        handle.write(f"sim3_scale={scale:.6f}\n")
        handle.write(f"trel_pct={trel:.6f}\n")
        handle.write(f"rrel_deg_per_100m={rrel:.6f}\n")
        handle.write(f"segments={segments}\n")
    print(f"Saved to {out}")


if __name__ == "__main__":
    main()
