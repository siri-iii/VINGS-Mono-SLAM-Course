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

---

## D13 Update (2026-05-31)

### What was done today

1. Ran imu_delay=0.0 sweep (config: ):
   - Result: ATE=61.41m, t_rel=78.81% — WORSE than delay=0.09 (61.14%)
   - VIO init scale with delay=0: s=0.306 vs delay=0.09: s=0.277 — both far from 1.0

2. Initially suspected a VIO data-rate limitation:
   - KITTI sync IMU file: 1106 rows = same as camera frames
   - IMU frequency: ~10 Hz (interval ≈ 0.100s), camera: ~9.6 Hz (interval ≈ 0.104s)
   - This was corrected on 2026-06-01: the paper explicitly evaluates KITTI Sync with 10 Hz IMU, so 10 Hz alone does not explain the metric gap.

3. Updated report notes (Section 10) and summary CSV

### Final deliverables status

| Item | Status |
| --- | --- |
| KITTI VO dense | t_rel=9.76%, ATE=13.04m — below target but presentable |
| KITTI VIO (best at the time) | t_rel=61.14%, ATE=64.62m — superseded by D14/D15 investigation |
| VIO delay sweep | delay=0.0 worse than 0.09 — confirmed not a timing issue |
| Waymo Scene01 | Blocked — data not on server |
| Report notes | Complete (Sections 1-10) |
| Summary CSV | Updated with all runs |

### Recommendation for presentation

Use VO dense as the primary result until the remaining public-reproduction gap is resolved. Do not present 10 Hz KITTI Sync IMU as the root cause; the paper uses the same nominal rate.


---

## D14 Update (2026-06-01)

1. Confirmed the installed vio-branch GTSAM exposes native `marginalizeOut`, `BA2GTSAM`, `GTSAM2BA`, and `CustomHessianFactor` bindings.
2. Removed the accidental Python override of `BA2GTSAM`; adapted its native augmented `[H | v]` return shape and routed visual factors through native `CustomHessianFactor`.
3. Kept a thin `marginalizeOut` guard that filters keys absent from either `Values` or the graph, then invokes native C++ marginalization.
4. Completed a full KITTI07 VIO rerun (`1106/1106`) without the previous segfault:
   - Result: `results/frontend/kitti07_vio/06-01-10-27-kitti_sync-kitti07_vio-`
   - Matched frames: `359`
   - ATE: `39.710914 m`
   - Sim3 scale: `0.874723`
   - `t_rel`: `23.189987%`
   - `r_rel`: `5.952185 deg/100m`
5. Checked interpolated per-frame evaluation: `t_rel=24.244406%`, close to sparse-keyframe evaluation. Timestamp alignment is not the remaining root cause.
6. Confirmed with NumPy that the staged metadata contains `1106` IMU rows and `1106` camera rows (about `10 Hz`; `wc -l` under-counts files without a trailing newline). The absence of unsynced high-rate OXTS is not sufficient to explain the remaining paper gap because the paper evaluates KITTI Sync at 10 Hz.

---

## D15 Update (2026-06-01)

1. Checked the original paper and official repository:
   - Paper Table III reports KITTI Sync sequence `07`: `t_rel=1.01%`, `r_rel=0.80 deg/100m`.
   - The paper explicitly states that KITTI Sync uses `10 Hz` IMU data.
   - Official sources: `https://arxiv.org/abs/2501.08286`, `https://github.com/Fudan-MAGIC-Lab/VINGS-Mono`, and `https://github.com/Fudan-MAGIC-Lab/VINGS-Mono/blob/main/docs/PREPARE_DATA.md`.
2. Downloaded the official `KITTI_Sync.zip` metadata package and compared SHA256 hashes. Server copies of `c2i.txt`, `calib.txt`, `camstamp.txt`, and `imu.txt` for `2011_09_30_drive_0027_sync` match the official package byte-for-byte.
3. Verified `ckpts/droid.pth` SHA256 matches the author-published Hugging Face file: `46476ef64cde45a97504910d6f3de2eef7b398ec1c6e4e668815c29076024526`.
4. Verified installed GTSAM is the README-recommended private fork branch: `Promethe-us/gtsam@c572c6f32` (`origin/vio`), with all four native bindings present.
5. Ran the author-provided `scripts/run_tracking.py` with the guarded compatibility path:
   - Result: `results/frontend/kitti07_vio/06-01-10-50-kitti_sync-kitti07_vio-_official_tracking`
   - ATE: `36.017960 m`
   - Sim3 scale: `0.931983`
   - `t_rel`: `20.840509%`
   - `r_rel`: `9.466777 deg/100m`
6. Ran the pre-shim author path in an isolated worktree at `a800d17`:
   - Result: `results/frontend/kitti07_vio/06-01-11-03-kitti_sync-kitti07_vio-_author_baseline`
   - ATE: `71.092135 m`
   - Sim3 scale: `0.004053`
   - `t_rel`: `72.732197%`
   - `r_rel`: `64.341415 deg/100m`
7. Ran a direct-native marginalization ablation while retaining the improved native visual-factor path:
   - Result: `results/frontend/kitti07_vio/06-01-11-13-kitti_sync-kitti07_vio-_direct_marg`
   - ATE: `78.373807 m`
   - Sim3 scale: `0.346670`
   - `t_rel`: `46.670746%`
   - `r_rel`: `9.769437 deg/100m`
8. Scanned raw-to-odometry GT offsets from `-8` to `+8` frames. The best guarded result remains about `20.82%`, so frame-index offset is not the cause.
9. Current conclusion:
   - Keep the guarded native compatibility path; it is the best tested public-repo path.
   - The remaining difference from the paper is not explained by timestamps, metadata contents, checkpoint contents, GTSAM branch, or 10 Hz KITTI Sync IMU.
   - The public repository does not include an official KITTI evaluation script or a reproducible command that reaches Table III. Ask the authors for the exact KITTI07 evaluation command, trajectory export path, and commit used for Table III before further parameter sweeps.
