"""
Person C — TSDF mesh export (paper Fig. 9).

VINGS-Mono only exports a Gaussian .ply; there is no surface mesh. This script
TSDF-fuses the per-keyframe rendered depth + pose dumped by a `debug_mode: True`
run (`<result_dir>/debug_dict/<frame>.pt` holding gt_c2w/gt_rgb/pred_depth/...)
into a triangle mesh using Open3D's ScalableTSDFVolume.

Intrinsics are read from the run's copied `config.yaml` and scaled from the full
sensor resolution down to the render resolution (frontend.image_size), matching the
loader convention [fv=fx, fu=fy, cv=cx, cu=cy].

Usage:
  python export_tsdf_mesh.py --result <result_dir> [--depth pred|gt] \
      [--voxel 0.05] [--trunc 0.3] [--max_depth 40] [--out mesh.ply]
"""
import argparse, glob, os
import numpy as np
import torch
import yaml
import open3d as o3d


def scaled_intrinsic(cfg):
    I = cfg["intrinsic"]
    H, W = int(I["H"]), int(I["W"])
    h, w = (int(cfg["frontend"]["image_size"][0]), int(cfg["frontend"]["image_size"][1]))
    u_scale, v_scale = h / H, w / W           # rows scale, cols scale (loader convention)
    fy = I["fu"] * u_scale                     # fu = fy
    fx = I["fv"] * v_scale                     # fv = fx
    cy = I["cu"] * u_scale                     # cu = cy
    cx = I["cv"] * v_scale                     # cv = cx
    return w, h, fx, fy, cx, cy


def to_hw3_uint8(rgb):
    a = rgb.detach().cpu().numpy() if torch.is_tensor(rgb) else np.asarray(rgb)
    if a.ndim == 3 and a.shape[0] in (3, 4):    # (C,H,W) -> (H,W,C)
        a = np.transpose(a[:3], (1, 2, 0))
    if a.max() <= 1.01:
        a = a * 255.0
    return np.ascontiguousarray(a[..., :3].clip(0, 255).astype(np.uint8))


def to_hw_float(depth):
    a = depth.detach().cpu().numpy() if torch.is_tensor(depth) else np.asarray(depth)
    a = np.squeeze(a)
    return np.ascontiguousarray(a.astype(np.float32))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--result", required=True)
    ap.add_argument("--depth", choices=["pred", "gt"], default="pred")
    ap.add_argument("--voxel", type=float, default=0.05)
    ap.add_argument("--trunc", type=float, default=0.3)
    ap.add_argument("--max_depth", type=float, default=40.0)
    ap.add_argument("--stride", type=int, default=1)
    ap.add_argument("--out", default=None)
    args = ap.parse_args()

    cfg = yaml.full_load(open(os.path.join(args.result, "config.yaml")))
    w, h, fx, fy, cx, cy = scaled_intrinsic(cfg)
    intr = o3d.camera.PinholeCameraIntrinsic(w, h, fx, fy, cx, cy)
    print(f"intrinsics @ {w}x{h}: fx={fx:.2f} fy={fy:.2f} cx={cx:.2f} cy={cy:.2f}")

    files = sorted(glob.glob(os.path.join(args.result, "debug_dict", "*.pt")))[:: args.stride]
    if not files:
        raise SystemExit(f"No debug_dict/*.pt in {args.result}. Run with debug_mode: True.")
    print(f"fusing {len(files)} frames ...")

    vol = o3d.pipelines.integration.ScalableTSDFVolume(
        voxel_length=args.voxel, sdf_trunc=args.trunc,
        color_type=o3d.pipelines.integration.TSDFVolumeColorType.RGB8)

    used = 0
    for f in files:
        d = torch.load(f, map_location="cpu")
        c2w = d["gt_c2w"].numpy() if torch.is_tensor(d["gt_c2w"]) else np.asarray(d["gt_c2w"])
        rgb = to_hw3_uint8(d["gt_rgb"])
        depth = to_hw_float(d["pred_depth" if args.depth == "pred" else "gt_depth"])
        if rgb.shape[:2] != depth.shape[:2]:
            continue
        depth[(depth <= 0) | (depth > args.max_depth)] = 0
        rgbd = o3d.geometry.RGBDImage.create_from_color_and_depth(
            o3d.geometry.Image(rgb), o3d.geometry.Image(depth),
            depth_scale=1.0, depth_trunc=args.max_depth, convert_rgb_to_intensity=False)
        vol.integrate(rgbd, intr, np.linalg.inv(c2w))   # extrinsic = w2c
        used += 1

    mesh = vol.extract_triangle_mesh()
    mesh.compute_vertex_normals()
    out = args.out or os.path.join(args.result, "tsdf_mesh.ply")
    o3d.io.write_triangle_mesh(out, mesh)
    print(f"fused {used} frames -> {out}")
    print(f"vertices={len(mesh.vertices)} triangles={len(mesh.triangles)}")


if __name__ == "__main__":
    main()
