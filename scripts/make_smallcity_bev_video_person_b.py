#!/usr/bin/env python3
"""Render a pure top-down SmallCity trajectory recording from saved keyframes."""
import argparse
import os

import cv2
import numpy as np

from eval_pose_dir import align_sim3, load_pose_dir


def fit_canvas(points, size, padding):
    lo, hi = points.min(0), points.max(0)
    span = np.maximum(hi - lo, 1e-6)
    scale = min((size - 2 * padding) / span[0], (size - 2 * padding) / span[1])

    def project(xy):
        px = padding + (xy[:, 0] - lo[0]) * scale
        py = size - padding - (xy[:, 1] - lo[1]) * scale
        return np.round(np.column_stack((px, py))).astype(np.int32)

    return project, lo, hi


def draw_polyline(image, points, color, thickness):
    if len(points) > 1:
        cv2.polylines(image, [points], False, color, thickness, cv2.LINE_AA)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("result_dir")
    parser.add_argument("gt_pose_dir")
    parser.add_argument("output_video")
    parser.add_argument("--final_png")
    parser.add_argument("--duration", type=float, default=120.0)
    parser.add_argument("--size", type=int, default=960)
    args = parser.parse_args()

    pred_idx, pred = load_pose_dir(os.path.join(args.result_dir, "droid_c2w"))
    gt_idx, gt = load_pose_dir(args.gt_pose_dir)
    if len(pred) == 0 or len(gt) == 0:
        raise SystemExit("Both prediction and GT directories must contain poses")
    gt_by_idx = {idx: pose for idx, pose in zip(gt_idx.tolist(), gt)}
    pairs = [(idx, pose, gt_by_idx[idx]) for idx, pose in zip(pred_idx.tolist(), pred) if idx in gt_by_idx]
    if not pairs:
        raise SystemExit("Prediction and GT directories have no overlapping frame IDs")

    frame_ids = np.array([item[0] for item in pairs], dtype=np.int64)
    pred_xyz = np.array([item[1][:3, 3] for item in pairs], dtype=np.float64)
    gt_xyz = np.array([item[2][:3, 3] for item in pairs], dtype=np.float64)
    full_gt_xyz = gt[:, :3, 3]
    scale, rot, trans = align_sim3(pred_xyz, gt_xyz)
    aligned_pred_xyz = (scale * (rot @ pred_xyz.T)).T + trans
    full_gt_xy, gt_xy, pred_xy = full_gt_xyz[:, :2], gt_xyz[:, :2], aligned_pred_xyz[:, :2]
    project, lo, hi = fit_canvas(np.vstack((full_gt_xy, pred_xy)), args.size, 80)
    full_gt_px, gt_px, pred_px = project(full_gt_xy), project(gt_xy), project(pred_xy)

    os.makedirs(os.path.dirname(args.output_video) or ".", exist_ok=True)
    fps = len(pairs) / args.duration
    writer = cv2.VideoWriter(args.output_video, cv2.VideoWriter_fourcc(*"mp4v"), fps, (args.size, args.size))
    if not writer.isOpened():
        raise SystemExit(f"Cannot open video writer for {args.output_video}")

    final_frame = None
    for current in range(1, len(pairs) + 1):
        image = np.full((args.size, args.size, 3), 248, dtype=np.uint8)
        for tick in np.linspace(lo[0], hi[0], 8):
            x = int(project(np.array([[tick, lo[1]]]))[0, 0])
            cv2.line(image, (x, 60), (x, args.size - 60), (225, 225, 225), 1)
        for tick in np.linspace(lo[1], hi[1], 8):
            y = int(project(np.array([[lo[0], tick]]))[0, 1])
            cv2.line(image, (60, y), (args.size - 60, y), (225, 225, 225), 1)
        draw_polyline(image, full_gt_px, (205, 205, 205), 2)
        draw_polyline(image, gt_px[:current], (150, 150, 150), 3)
        draw_polyline(image, pred_px[:current], (210, 85, 30), 4)
        cv2.circle(image, tuple(pred_px[current - 1]), 7, (30, 30, 220), -1, cv2.LINE_AA)
        cv2.putText(image, "SmallCity Mapping - Strict BEV", (40, 42), cv2.FONT_HERSHEY_SIMPLEX, 0.9, (35, 35, 35), 2, cv2.LINE_AA)
        cv2.putText(image, "GT trajectory", (40, args.size - 54), cv2.FONT_HERSHEY_SIMPLEX, 0.65, (130, 130, 130), 2, cv2.LINE_AA)
        cv2.putText(image, "Aligned estimate", (250, args.size - 54), cv2.FONT_HERSHEY_SIMPLEX, 0.65, (210, 85, 30), 2, cv2.LINE_AA)
        cv2.putText(image, f"keyframe {current}/{len(pairs)}  source frame {frame_ids[current - 1]}", (40, args.size - 22), cv2.FONT_HERSHEY_SIMPLEX, 0.58, (50, 50, 50), 1, cv2.LINE_AA)
        writer.write(image)
        final_frame = image
    writer.release()

    if args.final_png:
        os.makedirs(os.path.dirname(args.final_png) or ".", exist_ok=True)
        cv2.imwrite(args.final_png, final_frame)
    print(f"Wrote {len(pairs)} BEV frames at {fps:.6f} fps to {args.output_video}")


if __name__ == "__main__":
    main()
