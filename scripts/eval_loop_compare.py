"""
Person C — KITTI loop-closure on/off comparison.

Runs a paired evaluation of a loop-OFF and a loop-ON full-mapping run on the same
KITTI sequence: computes Sim(3)-aligned ATE / t_rel / r_rel for each, and draws a
top-down overlay of GT vs OFF vs ON trajectories (paper Fig. 10 style).

The full-mapping runner saves its final (loop-corrected) trajectory to
`<result_dir>/traj_final/<camera_timestamp>.txt` (added for Person C); if that is
absent it falls back to `<result_dir>/droid_c2w/`.

Usage:
  python eval_loop_compare.py --off <off_result_dir> --on <on_result_dir> --seq 07 \
         [--out_dir results/loop]
"""
import argparse, glob, os
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

from eval_kitti import load_gt_poses, align_sim3, apply_sim3, compute_ate, kitti_seq_errors

GT_DIR = "/root/autodl-tmp/data/kitti_gt/dataset/poses"
SEQ_TO_DRIVE = {"07": "0027", "08": "0028", "09": "0033"}


def camstamp_path(seq):
    drive = SEQ_TO_DRIVE[seq]
    return f"/root/autodl-tmp/data/kitti_raw/2011_09_30/2011_09_30_drive_{drive}_sync/metadata/camstamp.txt"


def load_camstamp_index(seq):
    data = np.loadtxt(camstamp_path(seq), dtype=str)
    return {round(float(row[0]), 6): idx for idx, row in enumerate(data)}


def load_traj(result_dir, seq):
    """Return (gt_indices, poses Nx4x4) matched to GT by camera timestamp."""
    for sub in ("traj_final", "droid_c2w"):
        c2w_dir = os.path.join(result_dir, sub)
        files = glob.glob(os.path.join(c2w_dir, "*.txt"))
        if files:
            break
    if not files:
        raise SystemExit(f"No trajectory files in {result_dir}/traj_final or /droid_c2w")
    ts2idx = load_camstamp_index(seq)
    matched = []
    for path in files:
        base = os.path.splitext(os.path.basename(path))[0]
        # loop writer may use '<int>.0' names; traj_final uses full timestamps
        ts = round(float(base), 6)
        gt_idx = ts2idx.get(ts)
        if gt_idx is None:
            gt_idx = ts2idx.get(round(float(int(float(base))), 6))
        if gt_idx is None:
            continue
        matched.append((gt_idx, np.loadtxt(path).reshape(4, 4)))
    matched.sort(key=lambda x: x[0])
    idx = np.array([m[0] for m in matched], dtype=np.int64)
    poses = np.array([m[1] for m in matched], dtype=np.float64)
    return idx, poses


def eval_one(result_dir, seq, gt_all):
    gt_idx, pred = load_traj(result_dir, seq)
    gt = gt_all[gt_idx]
    ate, scale = compute_ate(pred[:, :3, 3], gt[:, :3, 3])
    s, R, t = align_sim3(pred[:, :3, 3], gt[:, :3, 3])
    pred_aligned = apply_sim3(pred, s, R, t)
    trel, rrel, _ = kitti_seq_errors(gt, pred_aligned)
    return dict(n=len(pred), ate=ate, scale=scale, trel=trel, rrel=rrel,
                xyz=pred_aligned[:, :3, 3], gt_xyz=gt[:, :3, 3])


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--off")
    ap.add_argument("--on")
    ap.add_argument("--single", help="evaluate a single run (e.g. KITTI08 long) instead of an on/off pair")
    ap.add_argument("--seq", default="07")
    ap.add_argument("--out_dir", default=".")
    args = ap.parse_args()

    gt_all = load_gt_poses(args.seq)

    if args.single:
        r = eval_one(args.single, args.seq, gt_all)
        print(f"KITTI-{args.seq}: frames={r['n']}  ATE={r['ate']:.4f} m  "
              f"scale={r['scale']:.4f}  t_rel={r['trel']:.4f}%  r_rel={r['rrel']:.4f}")
        return

    if not (args.off and args.on):
        raise SystemExit("provide either --single <dir> or both --off <dir> --on <dir>")
    off = eval_one(args.off, args.seq, gt_all)
    on = eval_one(args.on, args.seq, gt_all)

    os.makedirs(args.out_dir, exist_ok=True)
    table = (
        f"KITTI-{args.seq} loop closure on/off\n"
        f"{'':10s}{'frames':>8s}{'ATE[m]':>10s}{'scale':>9s}{'t_rel[%]':>10s}{'r_rel':>9s}\n"
        f"{'OFF':10s}{off['n']:8d}{off['ate']:10.4f}{off['scale']:9.4f}{off['trel']:10.4f}{off['rrel']:9.4f}\n"
        f"{'ON':10s}{on['n']:8d}{on['ate']:10.4f}{on['scale']:9.4f}{on['trel']:10.4f}{on['rrel']:9.4f}\n"
        f"ATE improvement: {off['ate'] - on['ate']:.4f} m "
        f"({100*(off['ate']-on['ate'])/max(off['ate'],1e-9):.1f}% reduction)\n"
    )
    print(table)
    with open(os.path.join(args.out_dir, f"loop_compare_seq{args.seq}.txt"), "w") as f:
        f.write(table)

    # top-down overlay (KITTI camera frame: x right, z forward -> plot x vs z)
    plt.figure(figsize=(7, 7))
    plt.plot(on['gt_xyz'][:, 0], on['gt_xyz'][:, 2], 'k-', lw=2, label='GT')
    plt.plot(off['xyz'][:, 0], off['xyz'][:, 2], 'r--', lw=1.5, label=f"loop OFF (ATE {off['ate']:.2f}m)")
    plt.plot(on['xyz'][:, 0], on['xyz'][:, 2], 'b-', lw=1.5, label=f"loop ON (ATE {on['ate']:.2f}m)")
    plt.axis('equal'); plt.legend(); plt.grid(alpha=0.3)
    plt.title(f"KITTI-{args.seq}: NVS loop closure on/off")
    plt.xlabel('x [m]'); plt.ylabel('z [m]')
    out_png = os.path.join(args.out_dir, f"loop_correction_compare_seq{args.seq}.png")
    plt.savefig(out_png, dpi=150, bbox_inches='tight')
    print("saved", out_png)


if __name__ == "__main__":
    main()
