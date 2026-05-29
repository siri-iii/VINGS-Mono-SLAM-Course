# Person B Progress Log

Updated: 2026-05-29
Owner: Person B
Task package: 2D Gaussian Mapping Core

## Status Summary

Current status: B7 completed. B6 configs prepared but ablation runs not yet launched. B8 configs prepared but runs not yet launched. Safe to shut down after saving this state.

## Checklist

| ID | Task | Status | Updated | Notes |
| --- | --- | --- | --- | --- |
| B1 | Verify server and repository state | Done | 2026-05-28 | Repo, GPU, CUDA, conda env, PyTorch, and key imports checked |
| B2 | Locate Person B entrypoints | Done | 2026-05-28 | Entrypoints, adapted configs, data paths, output paths, and rasterizer import path identified |
| B3 | Run minimal environment smoke test | Done | 2026-05-28 | Hotel smoke ran to 142/405 frames under 180s timeout; environment, weights, data, tracker, and mapper verified |
| B4 | Run Hotel demo | Done | 2026-05-28 | Full Hotel run completed, exit 0, final PLY generated |
| B5 | Run Hierarchical-SmallCity demo | Done | 2026-05-28 | Full SmallCity run completed after adding missing looper config block, exit 0, final PLY generated |
| B6 | Score Manager ablation | Prepared | 2026-05-28 | Target ScanNet-0106 and Waymo-Scene13 data unavailable; prepared Hotel fallback configs for thresholds 0/0.8/12.8/25.6/102.4, not run yet |
| B7 | Sample Rasterizer profiling | Done | 2026-05-29 | profile_rasterizer_person_b.py ran 20 iters, 200k pts, 344x616; backward 5.36ms mean, total 7.06ms mean |
| B8 | Pose Refinement ablation | Pending | 2026-05-28 | Not started |
| B9 | Organize `docs/ABLATION.md` and `results/mapping/` | Pending | 2026-05-28 | Not started |
| B10 | Prepare PPT and recording material | Pending | 2026-05-28 | Not started |

## Activity Log

### 2026-05-28

- Created execution plan: `docs/PERSON_B_EXECUTION_PLAN.md`.
- Created progress log: `docs/PERSON_B_PROGRESS.md`.
- Completed B1 environment and repository verification.
- Saved the detailed B1 check log to `docs/person_b_b1_env_check.log`.
- Completed B2 entrypoint/config/data discovery.
- Saved the detailed B2 discovery log to `docs/person_b_b2_entrypoints.log`.
- Completed B3 Hotel smoke test with 180s timeout; run reached 142/405 frames and verified the full runtime stack.
- Completed B4 Hotel full demo; run finished all 405 frames with exit code 0.
- B4 outputs include final map `results/hotel/05-28-21-38-rtgslam-hote-_personB_full/ply/idx=404_2dgs.ply` and keyframe/rgbdnua outputs.
- First B5 SmallCity attempt failed immediately with `KeyError: looper` because `run.py` always constructs `LoopModel`.
- Added the missing `looper` block to `configs/hierarchical/smallcity.yaml`, reusing the verified LightGlue paths and thresholds from the Hotel config.
- Completed B5 SmallCity full demo; rerun finished all 877 frames with exit code 0.
- B5 outputs include final map `results/mapping/smallcity/05-28-22-09-hierarchical-smallcit-_personB_full_looperfix/ply/idx=876_2dgs.ply` and keyframe/rgbdnua outputs.
- Prepared B6 Score Manager fallback ablation on available Hotel data because ScanNet-0106 and Waymo-Scene13 data are unavailable on the server.
- Added B6 metric support: `metric_stdout: true` makes `num_of_gaussians` and `psnr` appear in run logs when wandb is disabled.
- Added configurable Score Manager prune upper threshold through `score_manager.prune_importance_upper`; default behavior remains `0.8` when unset.
- Generated B6 fallback configs under `configs/ablations/person_b/` for thresholds `0`, `0.8`, `12.8`, `25.6`, and `102.4`.
- B6 ablation runs were not launched before shutdown request.

## Environment Notes

Repository:

- Project path: `/root/autodl-tmp/VINGS-Mono-SLAM-Course`
- Branch state: `main...origin/main [ahead 6]`
- Remote: `git@github.com:siri-iii/VINGS-Mono-SLAM-Course.git`
- New untracked files from this task:
  - `docs/PERSON_B_EXECUTION_PLAN.md`
  - `docs/PERSON_B_PROGRESS.md`
  - `docs/person_b_b1_env_check.log`
- Existing untracked file before B1 completion:
  - `configs/kitti/kitti07_vo_240x800.yaml`

Submodules:

- `third_party/VINGS-Mono` is present and initialized.
- Recursive submodules are present, including `dbaf`, `diff-surfel-rasterization`, `gtsam`, and `metric_modules`.
- `third_party/VINGS-Mono` is checked out in detached HEAD state at `4d710b2`.

Server and GPU:

- OS login banner reports Ubuntu 22.04.5 LTS.
- GPU: NVIDIA GeForce RTX 4090.
- GPU memory reported by `nvidia-smi`: 49140 MiB.
- No GPU process was running during the B1 check.
- NVIDIA driver: 580.76.05.
- Driver CUDA capability reported by `nvidia-smi`: CUDA 13.0.

Python and CUDA environments:

- `base` environment is active by default but is not the project environment.
- `base` has Python 3.12.3 and PyTorch 2.8.0+cu128, but key project imports fail there.
- Correct project environment: `vings_vio`.
- `vings_vio` Python: 3.9.19.
- `vings_vio` PyTorch: 2.0.1+cu118.
- `vings_vio` CUDA availability: true.
- `vings_vio` sees GPU 0 as NVIDIA GeForce RTX 4090.
- `nvcc` is not on PATH by default, but exists at `/usr/local/cuda-12.8/bin/nvcc`.
- `CUDA_HOME` is unset in the current shell. This may need to be set before compiling or rebuilding extensions.

Key import check in `vings_vio` from `third_party/VINGS-Mono`:

- `torch_scatter`: OK
- `cv2`: OK
- `open3d`: OK
- `gtsam`: OK
- `lietorch`: OK
- `diff_gaussian_rasterization`: missing by direct import name
- `simple_knn._C`: missing by direct import name

Rasterizer/extension observations:

- `submodules/diff-surfel-rasterization` exists.
- A compiled extension exists at `submodules/diff-surfel-rasterization/diff_surfel_rasterization/_C.cpython-39-x86_64-linux-gnu.so`.
- Direct import by `diff_gaussian_rasterization` fails, but this may be expected because this repository uses `diff_surfel_rasterization` instead. B2 will confirm actual imports used by the mapping scripts.
- `simple_knn` was not found in the current repository scan and may not be required for this code path. B2 will confirm.


## Person B Entrypoint Notes

Main runnable entrypoint:

```bash
/root/miniconda3/envs/vings_vio/bin/python run.py <config.yaml> [--prefix <suffix>]
```

Expected working directory for execution:

```bash
/root/autodl-tmp/VINGS-Mono-SLAM-Course/third_party/VINGS-Mono/scripts
```

Required shell setup before running experiments:

```bash
conda activate vings_vio
export TORCH_LIB=/root/miniconda3/envs/vings_vio/lib/python3.9/site-packages/torch/lib
export LD_LIBRARY_PATH=$TORCH_LIB:${LD_LIBRARY_PATH:-}
export PYTHONPATH=/root/autodl-tmp/VINGS-Mono-SLAM-Course/third_party/VINGS-Mono/scripts:/root/autodl-tmp/VINGS-Mono-SLAM-Course/third_party/VINGS-Mono/scripts/frontend:/root/autodl-tmp/VINGS-Mono-SLAM-Course/third_party/VINGS-Mono/submodules/diff-surfel-rasterization:${PYTHONPATH:-}
```

Confirmed adapted configs in the course repository:

- Hotel: `/root/autodl-tmp/VINGS-Mono-SLAM-Course/configs/rtg/hotel.yaml`
- SmallCity: `/root/autodl-tmp/VINGS-Mono-SLAM-Course/configs/hierarchical/smallcity.yaml`
- Waymo01 frontend-only config exists, but it is not a B mapping demo: `/root/autodl-tmp/VINGS-Mono-SLAM-Course/configs/waymo/waymo01.yaml`

Confirmed B demo data:

- Hotel root: `/root/autodl-tmp/data/hotel/`
- Hotel loader: `datasets.rtgslam`
- Hotel frame count: 405
- SmallCity root: `/root/autodl-tmp/data/smallcity/small_city/`
- SmallCity loader: `datasets.hierarchical`
- SmallCity frame count: 877

Confirmed output paths from adapted configs:

- Hotel output root: `/root/autodl-tmp/VINGS-Mono-SLAM-Course/results/hotel/`
- SmallCity output root: `/root/autodl-tmp/VINGS-Mono-SLAM-Course/results/mapping/smallcity/`

Confirmed rasterizer import:

- The code imports `diff_surfel_rasterization`, not `diff_gaussian_rasterization`.
- `diff_surfel_rasterization` imports successfully after adding `third_party/VINGS-Mono/submodules/diff-surfel-rasterization` to `PYTHONPATH`.
- Main mapping code: `third_party/VINGS-Mono/scripts/gaussian/gaussian_model.py` and `gaussian_base.py`.
- Score Manager logic is in `scripts/gaussian/gaussian_model.py`, especially local/global score tracking and prune/split masks.

Candidate commands for B3/B4/B5:

Hotel smoke/full command:

```bash
cd /root/autodl-tmp/VINGS-Mono-SLAM-Course/third_party/VINGS-Mono/scripts
/root/miniconda3/envs/vings_vio/bin/python run.py /root/autodl-tmp/VINGS-Mono-SLAM-Course/configs/rtg/hotel.yaml --prefix _personB
```

SmallCity smoke/full command:

```bash
cd /root/autodl-tmp/VINGS-Mono-SLAM-Course/third_party/VINGS-Mono/scripts
/root/miniconda3/envs/vings_vio/bin/python run.py /root/autodl-tmp/VINGS-Mono-SLAM-Course/configs/hierarchical/smallcity.yaml --prefix _personB
```

Ablation data availability notes:

- ScanNet data for `ScanNet-0106` was not found under `/root/autodl-tmp/data`.
- Waymo `Scene13` data was not found under `/root/autodl-tmp/data`.
- The upstream config `third_party/VINGS-Mono/configs/waymo/Scene13.yaml` exists but still points to the author's original path and cannot run without data/path adaptation.
- B6 may need either data download, a documented blocker, or an adapted substitute experiment using available Hotel/SmallCity data.

## Command Log

B1 commands executed:

```bash
cd /root/autodl-tmp/VINGS-Mono-SLAM-Course
git status --short --branch
git remote -v
git submodule status --recursive
git rev-parse --show-toplevel
ls -la third_party/VINGS-Mono
git -C third_party/VINGS-Mono status --short --branch
git -C third_party/VINGS-Mono remote -v
conda env list
which python
python --version
nvidia-smi
which nvcc || true
nvcc --version || true
conda activate vings_vio
python --version
/usr/local/cuda-12.8/bin/nvcc --version
python - <<'PY'
# PyTorch and key import checks
PY
find . -maxdepth 5 \( -name '*.so' -o -name '*raster*' -o -name 'simple_knn*' -o -name '*gaussian*' \)
```

Detailed output saved to:

```text
docs/person_b_b1_env_check.log
```

## Result Paths

- B1 environment check log: `docs/person_b_b1_env_check.log`
- B2 entrypoint discovery log: `docs/person_b_b2_entrypoints.log`

- B3 Hotel smoke log: `results/mapping/person_b/logs/b3_hotel_smoke_20260528.log`
- B3 Hotel smoke output: `results/hotel/05-28-21-19-rtgslam-hote-_personB_smoke/`
- B4 Hotel full log: `results/mapping/person_b/logs/b4_hotel_full_20260528.log`
- B4 Hotel full output: `results/hotel/05-28-21-38-rtgslam-hote-_personB_full/`
- B4 Hotel final PLY: `results/hotel/05-28-21-38-rtgslam-hote-_personB_full/ply/idx=404_2dgs.ply` (~255 MB)
- B5 SmallCity failed first-attempt log: `results/mapping/person_b/logs/b5_smallcity_full_20260528.log`
- B5 SmallCity full log: `results/mapping/person_b/logs/b5_smallcity_full_looperfix_20260528.log`
- B5 SmallCity full output: `results/mapping/smallcity/05-28-22-09-hierarchical-smallcit-_personB_full_looperfix/`
- B5 SmallCity final PLY: `results/mapping/smallcity/05-28-22-09-hierarchical-smallcit-_personB_full_looperfix/ply/idx=876_2dgs.ply` (~1.72 GB)
- B6 fallback config directory: `configs/ablations/person_b/`
- B6 generated config: `configs/ablations/person_b/score_manager_hotel_t0.yaml`
- B6 generated config: `configs/ablations/person_b/score_manager_hotel_t0p8.yaml`
- B6 generated config: `configs/ablations/person_b/score_manager_hotel_t12p8.yaml`
- B6 generated config: `configs/ablations/person_b/score_manager_hotel_t25p6.yaml`
- B6 generated config: `configs/ablations/person_b/score_manager_hotel_t102p4.yaml`

## Blockers

No hard blocker for B1 through B5.

Resolved issues:

- B5 SmallCity needed a `looper` config block because `run.py` constructs `LoopModel` even when `use_loop` is absent. Added the block to `configs/hierarchical/smallcity.yaml`.
- ONNXRuntime CUDA provider reports missing `libcufft.so.10`, but both Hotel and SmallCity continued and completed successfully with fallback behavior.

Risks for B6 and later phases:

- The default `base` environment is not suitable for experiments; use `conda activate vings_vio`.
- `CUDA_HOME` and `PATH` may need CUDA 12.8 paths if any extension rebuild is required.
- Mapping scripts require `diff_surfel_rasterization` on `PYTHONPATH`; import works after adding the submodule path.
- Score Manager ablation target datasets `ScanNet-0106` and `Waymo-Scene13` are not currently present on the server.
- B6 fallback Hotel ablation configs are prepared but unexecuted; next session should run them and extract `[METRIC] num_of_gaussians` / `[METRIC] psnr` from logs.

### 2026-05-29

- Completed B7 Sample Rasterizer profiling.
- Ran  with 200k Gaussians, 20 iters, resolution 344×616, on RTX 4090 in vings_vio env.
- Results: backward_ms_mean=5.36ms, total_ms_mean=7.06ms.
- Saved raw JSON to .
- B6 ablation runs (5 Hotel threshold configs) and B8 pose refinement runs (3 strategies, hotel_personb_120) not yet launched.
- Next session: run B6 and B8 experiments, then B9 (ABLATION.md) and B10 (PPT material).
