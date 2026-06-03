"""
Person C — precompute per-frame dynamic-object masks for the frontend Dynamic Eraser.

The released VINGS-Mono code ships a FastSAM-based mask *builder* but never applies the
mask in the frontend BA. This script produces the masks the patched frontend consumes:
for every dataset frame it runs FastSAM (everything-segmentation) + dense optical flow,
and marks a segment as **dynamic** when its motion deviates from the camera-induced
(background) flow field. Masks are saved at the frontend feature resolution (H/8 x W/8)
so `depth_video.py` can multiply them straight into the per-edge confidence `weight`.

Output:  <dataset_root>/dynamic_masks/<frame_index>.npy   (float32, H/8 x W/8, 1=dynamic)
         <dataset_root>/dynamic_masks_viz/<frame_index>.png  (overlay, with --viz)

Usage (BONN example, on the server where FastSAM + GPU live):
  python gen_dynamic_masks.py --root /root/autodl-tmp/data/bonn/rgbd_bonn_person_tracking \
         --pattern 'color/*.jpg' --h8 48 --w8 64 --viz
"""
import argparse, glob, os
import numpy as np
import cv2


def load_fastsam(ckpt):
    from ultralytics import FastSAM
    return FastSAM(ckpt)


def fastsam_segments(model, img_bgr, device, imgsz=512):
    """Return (K, H, W) bool segment masks at the input image resolution."""
    res = model(img_bgr, device=device, retina_masks=True, imgsz=imgsz,
                conf=0.4, iou=0.9, verbose=False)
    r0 = res[0]
    if r0.masks is None:
        return np.zeros((0,) + img_bgr.shape[:2], dtype=bool)
    m = r0.masks.data.cpu().numpy().astype(bool)            # (K, h, w)
    if m.shape[1:] != img_bgr.shape[:2] and m.shape[0] > 0:
        m = np.stack([cv2.resize(s.astype(np.uint8), (img_bgr.shape[1], img_bgr.shape[0]),
                                 interpolation=cv2.INTER_NEAREST).astype(bool) for s in m])
    return m


def dynamic_mask_for_pair(model, prev_gray, cur_bgr, device, dev_ratio=2.5, min_seg_frac=0.0):
    """Mark segments whose median flow magnitude is >> background median flow as dynamic."""
    cur_gray = cv2.cvtColor(cur_bgr, cv2.COLOR_BGR2GRAY)
    H, W = cur_gray.shape
    dyn = np.zeros((H, W), dtype=bool)
    if prev_gray is None:
        return dyn
    flow = cv2.calcOpticalFlowFarneback(prev_gray, cur_gray, None,
                                        0.5, 3, 21, 3, 5, 1.2, 0)
    mag = np.linalg.norm(flow, axis=-1)                     # (H, W)
    bg_med = float(np.median(mag)) + 1e-6                   # camera-induced background motion
    segs = fastsam_segments(model, cur_bgr, device)
    for s in segs:
        n = int(s.sum())
        if n == 0 or n < min_seg_frac * H * W:
            continue
        seg_med = float(np.median(mag[s]))
        # dynamic if the segment moves markedly more than the background flow
        if seg_med > dev_ratio * bg_med and seg_med > 0.5:
            dyn |= s
    return dyn


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--root", required=True)
    ap.add_argument("--pattern", default="color/*.jpg")
    ap.add_argument("--ckpt", default=None, help="FastSAM-x.pt (default: repo ckpts/)")
    ap.add_argument("--device", default="cuda:0")
    ap.add_argument("--h8", type=int, default=48, help="frontend feature height (H/8)")
    ap.add_argument("--w8", type=int, default=64, help="frontend feature width  (W/8)")
    ap.add_argument("--dev_ratio", type=float, default=2.5)
    ap.add_argument("--viz", action="store_true")
    args = ap.parse_args()

    ckpt = args.ckpt
    if ckpt is None:
        here = os.path.dirname(os.path.abspath(__file__))
        ckpt = os.path.abspath(os.path.join(here, "..", "ckpts", "FastSAM-x.pt"))
    model = load_fastsam(ckpt)

    files = sorted(glob.glob(os.path.join(args.root, args.pattern)))
    out_dir = os.path.join(args.root, "dynamic_masks"); os.makedirs(out_dir, exist_ok=True)
    viz_dir = os.path.join(args.root, "dynamic_masks_viz")
    if args.viz: os.makedirs(viz_dir, exist_ok=True)
    print(f"{len(files)} frames -> {out_dir}  ({args.h8}x{args.w8})")

    prev_gray = None
    for i, f in enumerate(files):
        bgr = cv2.imread(f)
        dyn = dynamic_mask_for_pair(model, prev_gray, bgr, args.device, args.dev_ratio)
        small = cv2.resize(dyn.astype(np.uint8), (args.w8, args.h8),
                           interpolation=cv2.INTER_NEAREST).astype(np.float32)
        # frame index = position in sorted list (matches the loader's indexing)
        np.save(os.path.join(out_dir, f"{i}.npy"), small)
        if args.viz:
            ov = bgr.copy(); ov[dyn] = (0, 0, 255)
            cv2.imwrite(os.path.join(viz_dir, f"{i:06d}.png"), cv2.addWeighted(bgr, 0.6, ov, 0.4, 0))
        prev_gray = cv2.cvtColor(bgr, cv2.COLOR_BGR2GRAY)
        if i % 100 == 0:
            print(f"  {i}/{len(files)}  dyn_frac={float(small.mean()):.3f}", flush=True)
    print("done")


if __name__ == "__main__":
    main()
