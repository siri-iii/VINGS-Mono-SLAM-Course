#!/usr/bin/env python3
import argparse
import json
import statistics
import time

import torch
from diff_surfel_rasterization import GaussianRasterizationSettings, GaussianRasterizer


def cuda_ms(fn):
    torch.cuda.synchronize()
    start = torch.cuda.Event(enable_timing=True)
    end = torch.cuda.Event(enable_timing=True)
    start.record()
    out = fn()
    end.record()
    torch.cuda.synchronize()
    return start.elapsed_time(end), out


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--points", type=int, default=200000)
    parser.add_argument("--height", type=int, default=344)
    parser.add_argument("--width", type=int, default=616)
    parser.add_argument("--warmup", type=int, default=3)
    parser.add_argument("--iters", type=int, default=10)
    args = parser.parse_args()

    device = torch.device("cuda")
    torch.manual_seed(7)

    means3d = torch.empty(args.points, 3, device=device).uniform_(-1.0, 1.0)
    means3d[:, 2].uniform_(1.0, 6.0)
    means3d.requires_grad_(True)
    means2d = torch.zeros_like(means3d, requires_grad=True)
    colors = torch.rand(args.points, 3, device=device, requires_grad=True)
    opacities = torch.full((args.points, 1), 0.1, device=device, requires_grad=True)
    scales = torch.full((args.points, 2), 0.01, device=device, requires_grad=True)
    rotations = torch.zeros(args.points, 4, device=device)
    rotations[:, -1] = 1.0
    rotations.requires_grad_(True)
    scores = torch.zeros(args.points, 2, device=device)

    view = torch.eye(4, device=device)
    proj = torch.eye(4, device=device)
    settings = GaussianRasterizationSettings(
        image_height=args.height,
        image_width=args.width,
        tanfovx=0.55,
        tanfovy=0.55,
        bg=torch.zeros(3, device=device),
        scale_modifier=1.0,
        viewmatrix=view,
        projmatrix=proj,
        sh_degree=0,
        campos=torch.zeros(3, device=device),
        prefiltered=False,
        debug=False,
        pixel_mask=torch.ones(args.height * args.width, dtype=torch.bool, device=device),
    )
    rasterizer = GaussianRasterizer(settings)

    def one_iter():
        rendered, radii, depth = rasterizer(
            means3D=means3d,
            means2D=means2d,
            shs=None,
            colors_precomp=colors,
            opacities=opacities,
            scales=scales,
            rotations=rotations,
            scores=scores,
            cov3D_precomp=None,
        )
        loss = rendered.mean() + depth.mean()
        backward_ms, _ = cuda_ms(lambda: loss.backward())
        for tensor in (means3d, means2d, colors, opacities, scales, rotations):
            tensor.grad = None
        return backward_ms

    for _ in range(args.warmup):
        one_iter()

    backward = []
    total = []
    t0 = time.perf_counter()
    for _ in range(args.iters):
        total_ms, backward_ms = cuda_ms(one_iter)
        total.append(total_ms)
        backward.append(backward_ms)
    wall = time.perf_counter() - t0

    result = {
        "implementation": "diff_surfel_rasterization Sample Rasterizer",
        "points": args.points,
        "resolution": [args.height, args.width],
        "iters": args.iters,
        "backward_ms_mean": statistics.mean(backward),
        "backward_ms_median": statistics.median(backward),
        "total_ms_mean": statistics.mean(total),
        "total_ms_median": statistics.median(total),
        "wall_seconds": wall,
    }
    print("[PROFILE] " + json.dumps(result, sort_keys=True))


if __name__ == "__main__":
    main()
