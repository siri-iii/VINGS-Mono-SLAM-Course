"""Generate a lightweight KITTI-07 trajectory tracking MP4 from saved frontend poses."""
import argparse
import glob
import os

import cv2
import numpy as np

GT_DIR = "/root/autodl-tmp/data/kitti_gt/dataset/poses"
OUT_DIR = "/root/autodl-tmp/VINGS-Mono-SLAM-Course/media/videos"


def load_droid_xyz(result_dir):
    files = sorted(glob.glob(os.path.join(result_dir, "droid_c2w", "*.txt")))
    poses = [np.loadtxt(path).reshape(4, 4) for path in files]
    if not poses:
        return np.empty((0, 3), dtype=np.float64)
    return np.array([pose[:3, 3] for pose in poses], dtype=np.float64)


def load_gt_xyz(seq):
    raw = np.loadtxt(os.path.join(GT_DIR, f"{seq}.txt"))
    poses = raw.reshape(-1, 3, 4)
    return poses[:, :3, 3]


def align_umeyama(src, dst):
    mu_s, mu_d = src.mean(0), dst.mean(0)
    cov = ((dst - mu_d).T @ (src - mu_s)) / len(src)
    u, _, vt = np.linalg.svd(cov)
    s = np.eye(3)
    s[2, 2] = np.sign(np.linalg.det(u @ vt))
    r = u @ s @ vt
    t = mu_d - r @ mu_s
    return (r @ src.T).T + t


def project(points_xz, bounds, width, height, margin=56):
    min_x, max_x, min_z, max_z = bounds
    scale = min((width - 2 * margin) / max(max_x - min_x, 1e-6),
                (height - 2 * margin) / max(max_z - min_z, 1e-6))
    x = margin + (points_xz[:, 0] - min_x) * scale
    y = height - margin - (points_xz[:, 1] - min_z) * scale
    return np.column_stack([x, y]).astype(np.int32)


def draw_polyline(img, pts, color, end_idx, thickness=2):
    if end_idx < 2 or len(pts) < 2:
        return
    cv2.polylines(img, [pts[:end_idx]], False, color, thickness, lineType=cv2.LINE_AA)
    cv2.circle(img, tuple(pts[end_idx - 1]), 5, color, -1, lineType=cv2.LINE_AA)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--vo_dir", required=True)
    parser.add_argument("--vio_dir", required=True)
    parser.add_argument("--seq", default="07")
    parser.add_argument("--out", default=os.path.join(OUT_DIR, "tracking_kitti07.mp4"))
    args = parser.parse_args()

    gt = load_gt_xyz(args.seq)
    vo = load_droid_xyz(args.vo_dir)
    vio = load_droid_xyz(args.vio_dir)
    if len(vo) == 0 and len(vio) == 0:
        raise SystemExit("No frontend trajectories found")

    aligned = {"GT": gt}
    if len(vo):
        n = min(len(vo), len(gt))
        aligned["VO"] = align_umeyama(vo[:n], gt[:n])
    if len(vio):
        n = min(len(vio), len(gt))
        aligned["VIO"] = align_umeyama(vio[:n], gt[:n])

    all_xz = np.concatenate([xyz[:, [0, 2]] for xyz in aligned.values()], axis=0)
    pad = 8.0
    bounds = (all_xz[:, 0].min() - pad, all_xz[:, 0].max() + pad,
              all_xz[:, 1].min() - pad, all_xz[:, 1].max() + pad)

    width, height, fps = 1280, 720, 24
    os.makedirs(os.path.dirname(args.out), exist_ok=True)
    writer = cv2.VideoWriter(args.out, cv2.VideoWriter_fourcc(*"mp4v"), fps, (width, height))
    if not writer.isOpened():
        raise SystemExit("OpenCV could not open MP4 writer")

    pts = {name: project(xyz[:, [0, 2]], bounds, width, height) for name, xyz in aligned.items()}
    total = max(len(v) for v in pts.values())
    frames = 240
    colors = {"GT": (40, 40, 40), "VO": (230, 120, 40), "VIO": (55, 75, 230)}

    for frame in range(frames):
        img = np.full((height, width, 3), 255, np.uint8)
        cv2.putText(img, f"KITTI-{args.seq} frontend trajectory replay", (48, 48),
                    cv2.FONT_HERSHEY_SIMPLEX, 1.0, (30, 30, 30), 2, cv2.LINE_AA)
        cv2.putText(img, "Current run is diagnostic only; metrics are not target-valid.", (48, 84),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.62, (90, 90, 90), 1, cv2.LINE_AA)
        frac = (frame + 1) / frames
        for name in ["GT", "VO", "VIO"]:
            if name not in pts:
                continue
            end_idx = max(2, min(len(pts[name]), int(total * frac)))
            draw_polyline(img, pts[name], colors[name], end_idx)

        legend_x = width - 240
        for i, name in enumerate(["GT", "VO", "VIO"]):
            if name not in pts:
                continue
            y = 48 + i * 34
            cv2.line(img, (legend_x, y), (legend_x + 42, y), colors[name], 4, cv2.LINE_AA)
            cv2.putText(img, name, (legend_x + 56, y + 7), cv2.FONT_HERSHEY_SIMPLEX,
                        0.7, (45, 45, 45), 2, cv2.LINE_AA)
        writer.write(img)

    writer.release()
    print(args.out)


if __name__ == "__main__":
    main()
