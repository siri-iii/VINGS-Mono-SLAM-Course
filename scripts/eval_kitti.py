"""
评测 VINGS-Mono 在 KITTI-07 上的轨迹误差
输出 trel/rrel（论文表 III）以及 ATE（论文表 II）
用法: python eval_kitti.py <result_dir> [--seq 07]
"""
import numpy as np, os, argparse, glob

GT_DIR   = "/root/autodl-tmp/data/kitti_gt/dataset/poses"
CAMSTAMP = "/root/autodl-tmp/data/kitti_raw/2011_09_30/2011_09_30_drive_0027_sync/metadata/camstamp.txt"

def load_result_traj(result_dir):
    c2w_dir = os.path.join(result_dir, "droid_c2w")
    files = sorted(glob.glob(os.path.join(c2w_dir, "*.txt")))
    return np.array([np.loadtxt(f).reshape(4,4) for f in files])

def load_gt_poses(seq="07"):
    data = np.loadtxt(os.path.join(GT_DIR, f"{seq}.txt"))
    N = data.shape[0]; poses = np.zeros((N,4,4))
    poses[:,:3,:] = data.reshape(N,3,4); poses[:,3,3] = 1.
    return poses

def align_umeyama(src, dst):
    mu_s, mu_d = src.mean(0), dst.mean(0)
    cov = ((dst-mu_d).T @ (src-mu_s)) / len(src)
    U,D,Vt = np.linalg.svd(cov)
    S = np.eye(3); S[2,2] = np.sign(np.linalg.det(U@Vt))
    R = U@S@Vt; t = mu_d - R@mu_s
    return R, t

def compute_ate(pred_xyz, gt_xyz):
    R,t = align_umeyama(pred_xyz, gt_xyz)
    err = np.linalg.norm((R@pred_xyz.T).T+t - gt_xyz, axis=1)
    return float(np.sqrt(np.mean(err**2)))

def kitti_seq_errors(poses_gt, poses_est, lengths=(100,200,300,400,500,600,700,800)):
    n = min(len(poses_gt), len(poses_est))
    poses_gt, poses_est = poses_gt[:n], poses_est[:n]
    path_len = np.zeros(n)
    for i in range(1,n):
        path_len[i] = path_len[i-1] + np.linalg.norm(poses_gt[i,:3,3]-poses_gt[i-1,:3,3])
    def last_frame(start, length):
        for i in range(start,n):
            if path_len[i]-path_len[start] >= length: return i
        return -1
    t_errs, r_errs = [], []
    for start in range(0,n,max(1,n//50)):
        for L in lengths:
            end = last_frame(start,L)
            if end<0: continue
            dg = np.linalg.inv(poses_gt[start]) @ poses_gt[end]
            de = np.linalg.inv(poses_est[start]) @ poses_est[end]
            err = np.linalg.inv(dg) @ de
            seg = path_len[end]-path_len[start]
            t_errs.append(np.linalg.norm(err[:3,3])/seg*100)
            r_errs.append(np.degrees(np.arccos(np.clip((np.trace(err[:3,:3])-1)/2,-1,1)))/seg*100)
    return (float(np.mean(t_errs)) if t_errs else float("nan"),
            float(np.mean(r_errs)) if r_errs else float("nan"))

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("result_dir"); ap.add_argument("--seq", default="07")
    args = ap.parse_args()
    pred = load_result_traj(args.result_dir)
    gt   = load_gt_poses(args.seq)
    n    = min(len(pred), len(gt))
    print(f"Pred {len(pred)} / GT {len(gt)} / Using {n}")
    ate         = compute_ate(pred[:n,:3,3], gt[:n,:3,3])
    trel, rrel  = kitti_seq_errors(gt[:n], pred[:n])
    print(f"\n{=*38}\n  KITTI-{args.seq} Results\n{=*38}")
    print(f"  ATE  RMSE : {ate:.4f} m")
    print(f"  trel      : {trel:.4f} %   (paper target ≤1.5%)")
    print(f"  rrel      : {rrel:.4f} °/100m\n{=*38}")
    out = os.path.join(args.result_dir, "ate_trel_result.txt")
    open(out,"w").write(f"ATE_RMSE_m={ate:.6f}\ntrel_pct={trel:.6f}\nrrel_deg_per_100m={rrel:.6f}\n")
    print(f"Saved to {out}")

if __name__=="__main__": main()
