"""
Person C — BONN dynamic-scene ATE evaluation (Dynamic Eraser ablation, paper Table IV).

VINGS is monocular, so trajectories are up-to-scale: we Sim(3)-align the predicted
keyframe centers to BONN groundtruth before computing ATE RMSE (reported in cm),
matching how mono methods are scored.

The mapper saves final keyframe poses to `<result_dir>/traj_final/<frame_index>.txt`.
The BONN loader indexes frames by position in sorted `color/*.jpg`, whose filenames
are the original RGB timestamps, so frame_index -> timestamp -> GT association.

Single run:
  python eval_bonn.py --result <result_dir> --seq_dir /root/autodl-tmp/data/bonn/rgbd_bonn_balloon

Table IV (scans results/dynamic for <seq>_on / <seq>_off pairs):
  python eval_bonn.py --table --results_root results/dynamic --bonn_root /root/autodl-tmp/data/bonn
"""
import argparse, glob, os
import numpy as np


def align_sim3(src, dst):
    mu_s, mu_d = src.mean(0), dst.mean(0)
    x, y = src - mu_s, dst - mu_d
    cov = (y.T @ x) / len(src)
    u, s, vt = np.linalg.svd(cov)
    sign = np.eye(3); sign[2, 2] = np.sign(np.linalg.det(u @ vt))
    rot = u @ sign @ vt
    var = np.sum(x * x) / len(src)
    scale = np.trace(np.diag(s) @ sign) / var
    trans = mu_d - scale * rot @ mu_s
    return scale, rot, trans


def load_pred(result_dir):
    for sub in ("traj_final", "droid_c2w"):
        files = glob.glob(os.path.join(result_dir, sub, "*.txt"))
        if files:
            break
    if not files:
        raise SystemExit(f"No trajectory in {result_dir}")
    out = {}
    for p in files:
        fi = int(float(os.path.splitext(os.path.basename(p))[0]))
        out[fi] = np.loadtxt(p).reshape(4, 4)
    return out


def load_color_timestamps(seq_dir):
    files = sorted(glob.glob(os.path.join(seq_dir, "color", "*.jpg")))
    return [float(os.path.splitext(os.path.basename(f))[0]) for f in files]


def load_gt(seq_dir):
    gt = np.loadtxt(os.path.join(seq_dir, "groundtruth.txt"))
    return gt[:, 0], gt[:, 1:4]  # timestamps, xyz


def evaluate(result_dir, seq_dir, max_dt=0.05, interp=False):
    pred = load_pred(result_dir)
    color_ts = load_color_timestamps(seq_dir)
    gt_ts, gt_xyz = load_gt(seq_dir)
    pred_ts, pred_xyz = [], []
    for fi, c2w in pred.items():
        if fi < 0 or fi >= len(color_ts):
            continue
        pred_ts.append(color_ts[fi]); pred_xyz.append(c2w[:3, 3])
    pred_ts = np.array(pred_ts); pred_xyz = np.array(pred_xyz)
    order = np.argsort(pred_ts); pred_ts, pred_xyz = pred_ts[order], pred_xyz[order]
    if interp and len(pred_ts) >= 2:
        # per-frame protocol: interpolate keyframe positions to every GT timestamp in range
        lo, hi = pred_ts[0], pred_ts[-1]
        sel = (gt_ts >= lo) & (gt_ts <= hi)
        P = np.stack([np.interp(gt_ts[sel], pred_ts, pred_xyz[:, k]) for k in range(3)], axis=1)
        G = gt_xyz[sel]
    else:
        # association protocol: nearest pred keyframe <-> gt
        P, G = [], []
        for ts, xyz in zip(pred_ts, pred_xyz):
            j = int(np.argmin(np.abs(gt_ts - ts)))
            if abs(gt_ts[j] - ts) <= max_dt:
                P.append(xyz); G.append(gt_xyz[j])
        P, G = np.array(P), np.array(G)
    if len(P) < 5:
        return dict(n=len(P), ate_cm=float("nan"), scale=float("nan"))
    P = np.array(P); G = np.array(G)
    s, R, t = align_sim3(P, G)
    aligned = (s * (R @ P.T)).T + t
    ate = float(np.sqrt(np.mean(np.linalg.norm(aligned - G, axis=1) ** 2)))
    return dict(n=len(P), ate_cm=ate * 100.0, scale=s)


def _find_run(results_root, name):
    # run.py nests output as <results_root>/<name>/<runname>/{traj_final,...}.
    # Return the newest leaf dir whose path contains `name` and holds traj_final/ (or droid_c2w/).
    cands = []
    for root, dirs, _ in os.walk(results_root):
        if name in root and ("traj_final" in dirs or "droid_c2w" in dirs):
            cands.append(root)
    if not cands:
        return None
    return max(cands, key=lambda d: os.path.getmtime(d))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--result"); ap.add_argument("--seq_dir")
    ap.add_argument("--table", action="store_true")
    ap.add_argument("--results_root", default="results/dynamic")
    ap.add_argument("--bonn_root", default="/root/autodl-tmp/data/bonn")
    ap.add_argument("--interp", action="store_true", help="per-frame eval: interpolate keyframes to all GT timestamps")
    args = ap.parse_args()

    if not args.table:
        r = evaluate(args.result, args.seq_dir, interp=args.interp)
        print(f"matched={r['n']}  ATE={r['ate_cm']:.2f} cm  scale={r['scale']:.4f}")
        return

    seqs = [("ball", "balloon"), ("ps tk", "person_tracking"),
            ("ps tk2", "person_tracking2"), ("mv box2", "moving_nonobstructing_box2")]
    rows = []
    for label, name in seqs:
        seq_dir = os.path.join(args.bonn_root, f"rgbd_bonn_{name}")
        off_dir = _find_run(args.results_root, f"bonn_{name}_off")
        on_dir = _find_run(args.results_root, f"bonn_{name}_on")
        off = evaluate(off_dir, seq_dir, interp=args.interp)["ate_cm"] if off_dir else float("nan")
        on = evaluate(on_dir, seq_dir, interp=args.interp)["ate_cm"] if on_dir else float("nan")
        rows.append((label, off, on))
    print(f"\n{'BONN seq':12s}{'wo Eraser[cm]':>16s}{'w Eraser[cm]':>16s}")
    print("-" * 44)
    offs, ons = [], []
    for label, off, on in rows:
        print(f"{label:12s}{off:16.2f}{on:16.2f}")
        if np.isfinite(off): offs.append(off)
        if np.isfinite(on): ons.append(on)
    if offs and ons:
        print("-" * 44)
        print(f"{'Avg.':12s}{np.mean(offs):16.2f}{np.mean(ons):16.2f}")
    print("\nPaper Table IV (Ours w Eraser): ball 4.08 / ps tk 4.63 / ps tk2 5.05 / mv box2 3.58 / Avg 4.34")


if __name__ == "__main__":
    main()
