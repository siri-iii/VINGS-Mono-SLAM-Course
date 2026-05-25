# Member A Frontend Audit

Date: 2026-05-25

## Scope

Audited Member A's frontend reproduction task against `docs/REPRODUCTION_PLAN.md`: environment setup, KITTI/Waymo frontend VO/VIO runs, result artifacts under `results/frontend`, setup notes, and visual assets.

## Deliverable status

| Item | Status | Evidence |
| --- | --- | --- |
| Environment and setup notes | Mostly complete | `docs/SETUP.md`, experiment configs, and helper scripts are present. |
| KITTI 07 VO run | Runs, not target-valid | `results/frontend/kitti07_vo/05-23-23-06-kitti_sync-kitti07_vo-`, 233 predicted frames, ATE RMSE 26.183509 m, t_rel 93.686710%, r_rel 65.336528 deg/100m. |
| KITTI 07 VIO run | Runs after compatibility fixes, not target-valid | `results/frontend/kitti07_vio/05-25-17-08-kitti_sync-kitti07_vio-`, 736 predicted frames, ATE RMSE 12825.2790 m, t_rel 7160.8962%, r_rel 84.8615 deg/100m. |
| Waymo frontend run | Blocked | No Waymo dataset was found under `/root/autodl-tmp`; only configs/third-party references were present. |
| A visual assets | Completed with current data | `media/figures/traj_kitti07_compare.png`, `media/figures/vio_vs_vo_bar.png`, `media/videos/tracking_kitti07.mp4`. The MP4 is a trajectory replay generated from saved poses, not a raw tracker screen recording. |

## Fixes completed during audit

- Added frontend-only execution handling so KITTI frontend experiments can finish without requiring mapper/loop components.
- Added public-GTSAM compatibility fallbacks for marginalization and `GTSAM2BA` usage.
- Fixed active-graph insertion and guarded marginal-factor reuse when marginalization is unavailable.
- Preserved trajectory export in frontend-only runs through `droid_c2w` output.
- Enabled `frontend_only: True` in KITTI VO, KITTI VIO, and Waymo frontend configs.

## Assessment

Member A's task is only partially complete. The code path can now run the KITTI frontend experiments and produce expected artifact files, but the measured accuracy is far outside a publishable or target-valid reproduction. The current VIO result should be treated as a debugging baseline, not as a successful VIO reproduction, because it depends on compatibility fallbacks and skipped failed marginal factors.

Waymo remains incomplete until the actual dataset is staged on the server and the run is executed.

## Recommended next actions

1. Debug the KITTI pose convention, scale, timestamp alignment, and frontend-only trajectory export before presenting VO/VIO metrics.
2. Replace the compatibility fallback marginalization with the intended VINGS/GTSAM extension if available, or validate the public-GTSAM fallback numerically.
3. Stage Waymo data and run `configs/waymo/waymo01.yaml`.
4. Regenerate visual assets after the metrics are corrected.
