#!/usr/bin/env python3
import argparse
import json
import statistics
import time

import torch


def cuda_ms(fn):
    torch.cuda.synchronize()
    start = torch.cuda.Event(enable_timing=True)
    end = torch.cuda.Event(enable_timing=True)
    start.record()
    out = fn()
    end.record()
    torch.cuda.synchronize()
    return start.elapsed_time(end), out


def load_api(implementation):
    if implementation == "taming3dgs":
        from diff_gaussian_rasterization import GaussianRasterizationSettings, GaussianRasterizer
    else:
        from diff_surfel_rasterization import GaussianRasterizationSettings, GaussianRasterizer
    return GaussianRasterizationSettings, GaussianRasterizer


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--implementation", choices=("sample", "original_2dgs", "taming3dgs"), default="sample")
    parser.add_argument("--points", type=int, default=200000)
    parser.add_argument("--height", type=int, default=344)
    parser.add_argument("--width", type=int, default=616)
    parser.add_argument("--warmup", type=int, default=3)
    parser.add_argument("--iters", type=int, default=10)
    args = parser.parse_args()

    settings_type, rasterizer_type = load_api(args.implementation)
    device = torch.device("cuda")
    torch.manual_seed(7)

    means3d = torch.empty(args.points, 3, device=device).uniform_(-1.0, 1.0)
    means3d[:, 2].uniform_(1.0, 6.0)
    means3d.requires_grad_(True)
    means2d = torch.zeros_like(means3d, requires_grad=True)
    colors = torch.rand(args.points, 3, device=device, requires_grad=True)
    opacities = torch.full((args.points, 1), 0.1, device=device, requires_grad=True)
    scale_dims = 3 if args.implementation == "taming3dgs" else 2
    scales = torch.full((args.points, scale_dims), 0.01, device=device, requires_grad=True)
    rotations = torch.zeros(args.points, 4, device=device)
    rotations[:, -1] = 1.0
    rotations.requires_grad_(True)
    scores = torch.zeros(args.points, 2, device=device)

    settings_args = dict(
        image_height=args.height,
        image_width=args.width,
        tanfovx=0.55,
        tanfovy=0.55,
        bg=torch.zeros(3, device=device),
        scale_modifier=1.0,
        viewmatrix=torch.eye(4, device=device),
        projmatrix=torch.eye(4, device=device),
        sh_degree=0,
        campos=torch.zeros(3, device=device),
        prefiltered=False,
        debug=False,
    )
    if args.implementation == "sample":
        settings_args["pixel_mask"] = torch.ones(args.height * args.width, dtype=torch.bool, device=device)
    rasterizer = rasterizer_type(settings_type(**settings_args))

    tensors = (means3d, means2d, colors, opacities, scales, rotations)

    def one_iter():
        kwargs = dict(
            means3D=means3d,
            means2D=means2d,
            shs=None,
            colors_precomp=colors,
            opacities=opacities,
            scales=scales,
            rotations=rotations,
            cov3D_precomp=None,
        )
        if args.implementation == "sample":
            kwargs["scores"] = scores
        outputs = rasterizer(**kwargs)
        loss = outputs[0].mean()
        backward_ms, _ = cuda_ms(lambda: loss.backward())
        for tensor in tensors:
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
        "implementation": args.implementation,
        "points": args.points,
        "resolution": [args.height, args.width],
        "iters": args.iters,
        "loss": "rendered_rgb_mean",
        "backward_ms_mean": statistics.mean(backward),
        "backward_ms_median": statistics.median(backward),
        "total_ms_mean": statistics.mean(total),
        "total_ms_median": statistics.median(total),
        "wall_seconds": wall,
    }
    print("[PROFILE] " + json.dumps(result, sort_keys=True))


if __name__ == "__main__":
    main()
