"""
A2: KITTI-07 轨迹对比图 (ours vs GT)
A3: mono-only vs mono+IMU ATE/trel 柱状图

用法:
  python plot_traj.py --vo_dir <kitti07_vo_result> [--vio_dir <kitti07_vio_result>]
  输出: media/figures/traj_kitti07_compare.png
        media/figures/vio_vs_vo_bar.png
"""
import numpy as np, matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import os, argparse, glob

GT_DIR   = "/root/autodl-tmp/data/kitti_gt/dataset/poses"
MEDIA    = "/root/autodl-tmp/VINGS-Mono-SLAM-Course/media/figures"
os.makedirs(MEDIA, exist_ok=True)

# ── helpers ──────────────────────────────────────────────────────────
def load_droid_traj(result_dir):
    files = sorted(glob.glob(os.path.join(result_dir, "droid_c2w", "*.txt")))
    return np.array([np.loadtxt(f).reshape(4,4) for f in files])

def load_gt(seq="07"):
    d = np.loadtxt(os.path.join(GT_DIR, f"{seq}.txt"))
    N = d.shape[0]; P = np.zeros((N,4,4))
    P[:,:3,:] = d.reshape(N,3,4); P[:,3,3] = 1.
    return P

def align_umeyama(src, dst):
    mu_s, mu_d = src.mean(0), dst.mean(0)
    cov = ((dst-mu_d).T @ (src-mu_s)) / len(src)
    U,D,Vt = np.linalg.svd(cov)
    S = np.eye(3); S[2,2] = np.sign(np.linalg.det(U@Vt))
    R = U@S@Vt; t = mu_d - R@mu_s
    return R, t

def align_xyz(pred_xyz, gt_xyz):
    R, t = align_umeyama(pred_xyz, gt_xyz)
    return (R @ pred_xyz.T).T + t

def ate(pred_xyz, gt_xyz):
    a = align_xyz(pred_xyz, gt_xyz)
    return float(np.sqrt(np.mean(np.linalg.norm(a - gt_xyz, axis=1)**2)))

def read_eval(result_dir):
    f = os.path.join(result_dir, "ate_trel_result.txt")
    if not os.path.exists(f): return {}
    d = {}
    for line in open(f):
        k,v = line.strip().split("=")
        d[k] = float(v)
    return d

# ── plot A2: trajectory comparison ──────────────────────────────────
def plot_traj(vo_dir, vio_dir=None, seq="07"):
    gt = load_gt(seq)
    gt_xyz = gt[:, :3, 3]
    fig, ax = plt.subplots(1,1, figsize=(9,6))

    ax.plot(gt_xyz[:,0], gt_xyz[:,2], "k-", lw=2, label="Ground Truth")

    vo_poses = load_droid_traj(vo_dir)
    n = min(len(vo_poses), len(gt))
    vo_al = align_xyz(vo_poses[:n,:3,3], gt_xyz[:n])
    ax.plot(vo_al[:,0], vo_al[:,2], "b-", lw=1.5, label=f"VINGS-Mono VO (ATE={ate(vo_poses[:n,:3,3], gt_xyz[:n]):.2f}m)")

    if vio_dir and os.path.exists(vio_dir):
        vio_poses = load_droid_traj(vio_dir)
        n2 = min(len(vio_poses), len(gt))
        vio_al = align_xyz(vio_poses[:n2,:3,3], gt_xyz[:n2])
        ax.plot(vio_al[:,0], vio_al[:,2], "r-", lw=1.5, label=f"VINGS-Mono VIO (ATE={ate(vio_poses[:n2,:3,3], gt_xyz[:n2]):.2f}m)")

    ax.set_xlabel("X (m)"); ax.set_ylabel("Z (m)")
    ax.set_title(f"KITTI-{seq} Trajectory Comparison")
    ax.legend(); ax.set_aspect("equal"); ax.grid(True, alpha=0.3)
    plt.tight_layout()
    out = os.path.join(MEDIA, "traj_kitti07_compare.png")
    plt.savefig(out, dpi=150, bbox_inches="tight"); plt.close()
    print(f"Saved A2: {out}")

# ── plot A3: VO vs VIO bar chart ─────────────────────────────────────
def plot_bar(vo_dir, vio_dir=None):
    vo  = read_eval(vo_dir) if vo_dir else {}
    vio = read_eval(vio_dir) if vio_dir else {}

    labels = ["ATE (m)", "trel (%)", "rrel (°/100m)"]
    keys   = ["ATE_RMSE_m", "trel_pct", "rrel_deg_per_100m"]
    x = np.arange(len(labels)); w = 0.3

    fig, ax = plt.subplots(figsize=(8,5))
    bars1 = [vo.get(k, 0)  for k in keys]
    bars2 = [vio.get(k, 0) for k in keys]

    ax.bar(x - w/2, bars1, w, label="Mono-only (VO)",  color="#4e9af1", alpha=0.85)
    ax.bar(x + w/2, bars2, w, label="Mono+IMU (VIO)",  color="#f17a4e", alpha=0.85)

    for i,(v1,v2) in enumerate(zip(bars1,bars2)):
        if v1>0: ax.text(i-w/2, v1+0.005*max(bars1+bars2), f"{v1:.3f}", ha="center", fontsize=8)
        if v2>0: ax.text(i+w/2, v2+0.005*max(bars1+bars2), f"{v2:.3f}", ha="center", fontsize=8)

    ax.set_xticks(x); ax.set_xticklabels(labels)
    ax.set_title("KITTI-07: Mono-only vs Mono+IMU (VINGS-Mono)")
    ax.legend(); ax.grid(axis="y", alpha=0.3)
    plt.tight_layout()
    out = os.path.join(MEDIA, "vio_vs_vo_bar.png")
    plt.savefig(out, dpi=150, bbox_inches="tight"); plt.close()
    print(f"Saved A3: {out}")

# ── main ─────────────────────────────────────────────────────────────
if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--vo_dir",  default=None)
    ap.add_argument("--vio_dir", default=None)
    ap.add_argument("--seq",     default="07")
    args = ap.parse_args()

    if args.vo_dir is None:
        # 自动找最新结果
        dirs = sorted(glob.glob("/root/autodl-tmp/VINGS-Mono-SLAM-Course/results/frontend/kitti07_vo/*/"))
        if dirs: args.vo_dir = dirs[-1]
    if args.vio_dir is None:
        dirs = sorted(glob.glob("/root/autodl-tmp/VINGS-Mono-SLAM-Course/results/frontend/kitti07_vio/*/"))
        if dirs: args.vio_dir = dirs[-1]

    print(f"VO  dir: {args.vo_dir}")
    print(f"VIO dir: {args.vio_dir}")

    if args.vo_dir:
        plot_traj(args.vo_dir, args.vio_dir, args.seq)
        plot_bar(args.vo_dir, args.vio_dir)
    else:
        print("No result dir found. Run experiments first.")
