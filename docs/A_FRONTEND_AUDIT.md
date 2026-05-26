# Member A Frontend Audit

Date: 2026-05-26

## Scope

Audited and continued Member A's frontend reproduction task from `docs/REPRODUCTION_PLAN.md`: AutoDL environment, KITTI-07 VO/VIO, Waymo Scene01 VO, frontend metrics, and A visual assets.

## Current deliverable status

| Item | Status | Evidence |
| --- | --- | --- |
| Environment and setup notes | Mostly complete | `docs/SETUP.md`, configs, local conda env, and helper scripts are present. |
| KITTI-07 VO | Runs, below target | Best run: `results/frontend/kitti07_vo_dense/05-25-17-33-kitti_sync-kitti07_vo_dense-`, 727 matched frames, ATE 13.043128 m, t_rel 9.759937%, r_rel 3.002223 deg/100m. Target t_rel is <= 1.5%. |
| KITTI-07 VIO | Runs after GTSAM guard, failed accuracy | Latest guarded run: `results/frontend/kitti07_vio/05-26-14-32-kitti_sync-kitti07_vio-`, 346 matched frames, ATE 64.620664 m, t_rel 61.143212%, r_rel 24.544240 deg/100m. Native vio-branch `marginalizeOut` segfaulted around frame 80, so the compatibility layer now uses the Python fallback for marginalization while preserving native `GTSAM2BA`. |
| Waymo Scene01 VO | Blocked | `scripts/check_frontend_data.py` reports missing `/root/autodl-tmp/data/waymo/Scene01/{color,pose}`. No Waymo data exists on this server. |
| A visual assets | Present | `media/figures/traj_kitti07_compare.png`, `media/figures/vio_vs_vo_bar.png`, `media/videos/tracking_kitti07.mp4`. The MP4 is a trajectory replay from saved poses, not a raw tracker GUI recording. |
| Metrics table | Present | `results/frontend/a_frontend_summary.csv`. |

## Work completed after audit

- Fixed KITTI evaluation to match frontend outputs to GT by camera timestamp instead of positional row order.
- Regenerated KITTI VO/VIO metrics with timestamp matching.
- Added dense KITTI configs with `keyframe_thresh: 1.0` and reran both VO and VIO.
- Regenerated A2/A3 figures and A1 MP4 from the dense runs.
- Added `scripts/check_frontend_data.py` for explicit KITTI/Waymo data validation.
- Added `scripts/eval_waymo.py` so Waymo Scene01 can be evaluated immediately after data is staged.
- Kept the frontend-only compatibility fixes in `third_party/VINGS-Mono` so the runs complete without mapper/loop components.
- Installed/tested the vio-branch GTSAM bindings and guarded `gtsam.marginalizeOut` after reproducing a native segmentation fault in `depth_video.py:1792`; the guarded KITTI07 VIO run now completes.

## Metric summary

| Run | Frames | ATE RMSE (m) | t_rel (%) | r_rel (deg/100m) | Status |
| --- | ---: | ---: | ---: | ---: | --- |
| KITTI07 VO original | 233 | 19.485853 | 14.171275 | 3.201596 | Below target |
| KITTI07 VO dense | 727 | 13.043128 | 9.759937 | 3.002223 | Best VO, below target |
| KITTI07 VIO original | 736 | 72.524843 | 63.152289 | 65.343844 | Failed accuracy |
| KITTI07 VIO dense | 737 | 72.210345 | 68.725937 | 65.566344 | Failed accuracy |
| KITTI07 VIO guarded native GTSAM | 346 | 64.620664 | 61.143212 | 24.544240 | Runs, failed accuracy |

## Assessment

Member A's task is not fully successful on the scientific targets. The code now runs the KITTI frontend experiments and produces the requested result files, figures, and replay video, but the KITTI metrics are far outside the reproduction target. Dense keyframes improve VO, but not enough. VIO no longer crashes with the guarded marginalization path, but it still needs deeper repair in the IMU initialization, calibration/extrinsic chain, and marginalization quality rather than another small config change.

Waymo cannot be completed on this server until the dataset is staged. The expected structure is:

```text
/root/autodl-tmp/data/waymo/Scene01/
  color/*.jpg
  pose/*.txt
```

After data is present, run:

```bash
python scripts/check_frontend_data.py
/root/run_waymo_exp.sh
python scripts/eval_waymo.py <latest results/frontend/waymo01 run dir>
```

## Remaining blockers

1. Waymo Scene01 data is absent from the server.
2. KITTI VIO depends on compatibility fallbacks for private GTSAM extension APIs; native `marginalizeOut` crashes and the Python fallback lets the run finish but does not reproduce the intended estimator quality.
3. KITTI VO/VIO accuracy is still below target even with timestamp-correct evaluation, dense keyframes, and guarded GTSAM VIO bindings.
