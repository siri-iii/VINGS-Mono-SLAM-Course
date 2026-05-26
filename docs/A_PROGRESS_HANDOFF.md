# A Progress Handoff

Date: 2026-05-26

Purpose: short resume note for continuing Person A frontend work after server shutdown/restart.

## Current Status

Person A frontend/system task is usable for group handoff but not scientifically solved.

Completed:
- Server repo and `vings_vio` environment are usable.
- KITTI07 VO/VIO frontend runs can be launched and evaluated.
- KITTI evaluation now matches predictions to GT by camera timestamp.
- VIO GTSAM crash was diagnosed and guarded.
- A report/audit notes exist for presentation and handoff.
- B/C/D are not blocked by A and can start their own work.

Not completed:
- KITTI07 VO/VIO metrics are still far from paper target.
- Waymo Scene01 remains blocked because dataset is absent.
- AutoDL image/snapshot ID is not recorded in repo.

## Important Files

Read these first after resuming:
- `docs/A_FRONTEND_AUDIT.md`
- `docs/A_FRONTEND_REPORT_NOTES.md`
- `results/frontend/a_frontend_summary.csv`
- `third_party/VINGS-Mono/scripts/frontend/gtsam_compat.py`
- `scripts/eval_kitti.py`
- `docs/SETUP.md`

## Commits Already Made

Main repo:
- `329649e Add member A frontend report notes`
- `9bc8384 Record member A guarded VIO run`
- `c56990f Add timestamp-matched frontend evaluation`
- `6dd7f49 Complete member A frontend audit artifacts`

VINGS-Mono submodule:
- `4d710b2 Guard VIO GTSAM marginalization`
- `1a8ebe4 Fix frontend-only VIO run path`

## Latest Metrics

Best/current useful records:

| Run | Result dir | Frames | ATE RMSE (m) | t_rel (%) | r_rel (deg/100m) | Notes |
| --- | --- | ---: | ---: | ---: | ---: | --- |
| VO dense | `results/frontend/kitti07_vo_dense/05-25-17-33-kitti_sync-kitti07_vo_dense-` | 727 | 13.043129 | 9.759864 | 3.002179 | Best VO so far |
| VIO guarded | `results/frontend/kitti07_vio/05-26-14-32-kitti_sync-kitti07_vio-` | 346 | 64.620696 | 61.143249 | 24.544249 | VIO runs after guarded marginalization |
| VIO dense native G2B + safe marg | `results/frontend/kitti07_vio_dense/05-26-15-25-kitti_sync-kitti07_vio_dense-_native_g2b_safe_marg` | 734 | 67.441901 | 75.634691 | 39.358509 | Runs, but no accuracy improvement |
| VO 240x800 test | `results/frontend/kitti07_vo_240x800/05-26-15-52-kitti_sync-kitti07_vo_240x800-` | 830 | 26.390295 | 16.738205 | 1.708722 | More frames and better r_rel, worse ATE/t_rel |

Paper target for KITTI07 t_rel is around <= 1.5%; not achieved.

## Technical Findings

1. KITTI evaluation bug fixed:
   - Frontend pose filenames are camera timestamps.
   - `scripts/eval_kitti.py` maps timestamps through KITTI `camstamp.txt` instead of row-order pairing.

2. GTSAM private API issue:
   - VINGS-Mono VIO depends on private/forked GTSAM APIs: `marginalizeOut`, `GTSAM2BA`, `BA2GTSAM`, `CustomHessianFactor`, `CombinedImuFactor.evaluateErrorCustom`.
   - GTSAM submodule was checked out to vio branch commit `c572c6f321621adac01fc70f1020d0daa640df19`.
   - Native `GTSAM2BA` is preserved.
   - Native `marginalizeOut` segfaulted around frame 80 at `depth_video.py:1792`.
   - `gtsam_compat.py` now forces `gtsam.marginalizeOut` to Python fallback to avoid the crash.

3. KITTI intrinsics note:
   - Config names are confusing: code uses `[fv, fu, cv, cu]`, where `cv` is actually x/cx and `cu` is y/cy.
   - Current values match metadata: fx=707.0912, fy=707.0912, cx=601.8873, cy=183.1104.
   - Do not blindly swap `cu/cv`.

4. Coordinate/evaluation variants were checked:
   - Existing saved `c2w` interpretation is the best among quick c2w/w2c/axis flip variants.
   - No evidence yet that evaluation direction alone explains bad metrics.

## Uncommitted/Temporary State

At time of writing, expected dirty status:
- `?? configs/kitti/kitti07_vo_240x800.yaml`
- `docs/A_PROGRESS_HANDOFF.md` will be newly added by this note.

`configs/kitti/kitti07_vo_240x800.yaml` is a temporary experiment config generated from dense VO with `image_size: [240, 800]`. It did not improve ATE/t_rel, but can be kept for future reference or removed later.

## Next Steps For A

When continuing A, prioritize:

1. Decide whether to keep or remove `configs/kitti/kitti07_vo_240x800.yaml`.
2. Investigate VIO metric failure:
   - IMU/camera extrinsic `metadata/c2i.txt` direction.
   - `dataset.imu_delay` sweep around 0.0, 0.05, 0.09, 0.10.
   - VIO initialization logs: scale, gravity, bias values after `V-I successfully initialized!`.
   - Whether frontend-only saving omits/changes final optimized trajectory compared with full mapping mode.
3. If data is staged, run Waymo Scene01:
   - Expected path: `/root/autodl-tmp/data/waymo/Scene01/{color,pose}`.
   - Commands: `python scripts/check_frontend_data.py`, `/root/run_waymo_exp.sh`, `python scripts/eval_waymo.py <result_dir>`.
4. If no time remains, use `docs/A_FRONTEND_REPORT_NOTES.md` for presentation and state metrics honestly.

## Useful Commands

Check state:

```bash
cd /root/autodl-tmp/VINGS-Mono-SLAM-Course
git status --short
git -C third_party/VINGS-Mono status --short
```

Evaluate a KITTI result:

```bash
source /root/miniconda3/etc/profile.d/conda.sh
conda activate vings_vio
cd /root/autodl-tmp/VINGS-Mono-SLAM-Course
python scripts/eval_kitti.py <result_dir>
```

Run KITTI experiment manually:

```bash
cd /root/autodl-tmp/VINGS-Mono-SLAM-Course/third_party/VINGS-Mono/scripts
export LD_LIBRARY_PATH=/root/miniconda3/envs/vings_vio/lib/python3.9/site-packages/torch/lib:$LD_LIBRARY_PATH
export PYTHONPATH=/root/autodl-tmp/VINGS-Mono-SLAM-Course/third_party/VINGS-Mono/scripts:/root/autodl-tmp/VINGS-Mono-SLAM-Course/third_party/VINGS-Mono/scripts/frontend:$PYTHONPATH
/root/miniconda3/envs/vings_vio/bin/python run.py /root/autodl-tmp/VINGS-Mono-SLAM-Course/configs/kitti/kitti07_vio.yaml
```
