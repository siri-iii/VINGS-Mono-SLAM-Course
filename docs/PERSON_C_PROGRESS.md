# Person C Progress — NVS Loop Closure + Dynamic Eraser + Long Sequence + Mesh

Owner: C (henry). Date: 2026-06-02.
PPT theme: "大场景一致性：NVS 回环检测 + 动态物体擦除".

All experiments run on the **AutoDL server** (`ssh Slam`, repo at
`/root/autodl-tmp/VINGS-Mono-SLAM-Course`, env `vings_vio`). The local RTX 5060 Ti is
Blackwell (sm_120) and cannot run the official torch 2.0.1+cu118 stack, so it is used
only for editing / light plotting.

---

## 1. Status

| Deliverable | Prep (no-GPU) | Data | GPU run |
| --- | --- | --- | --- |
| Loop on/off comparison (Fig 10) | configs + eval + run.py traj-save ready | seq07 **on server** | ready |
| KITTI long-trajectory + loop | same seq07 run doubles as this | seq07 **on server** | ready |
| TSDF mesh export (Fig 9) | mesh config + export script ready | Waymo Scene13 **on server** | ready |
| BONN Dynamic Eraser ablation (Table IV) | configs + code integration + eval ready | downloading (~1h) | pending data + runs |
| KITTI08 3.2km (Fig 8) — stretch | `kitti08_long.yaml` ready | seq08 best-effort (S3 ~24KB/s, may not finish) | optional |

Prep done in **no-GPU** mode. **Long GPU runs wait for explicit go-ahead** (paid GPU).

> Data note: this AutoDL instance has very slow international bandwidth to AWS S3
> (KITTI raw, ~24–45 KB/s), so the full seq08 (4.23 GB) is impractical (~26 h). The loop
> on/off + long-trajectory deliverable therefore uses **seq07** (1101 frames, ~700 m,
> already staged, has a real end→start loop). BONN (uni-bonn) downloads at ~270 KB/s and
> is feasible. A best-effort seq08 carve is queued to resume after BONN (tmux `seq08`); if
> it completes, run `kitti08_long.yaml` for the 3.2 km headline.

## 2. Code changes (submodule `third_party/VINGS-Mono`, originals saved as `*.orig_personC`)

1. **`scripts/dynamic/dynamic_utils.py`** — rewritten: removed hardcoded `/data/wuke/...`
   paths; FastSAM ckpt auto-resolved to repo `ckpts/FastSAM-x.pt`; uses `ultralytics`
   FastSAM (installed `--no-deps`, torch/numpy untouched); added
   `get_dynamic_mask_cached()` (FastSAM segments × high re-render-residual → dynamic mask,
   cached per keyframe).
2. **`scripts/gaussian/loss_utils.py`** (`get_loss`) — ANDs `gt_dict['dynamic_mask']` into
   `valid_mask` so dynamic pixels are excluded from rgb/depth/normal/alpha losses.
3. **`scripts/gaussian/gaussian_base.py`** (`train_once_gaussian`) — when `use_dynamic`,
   lazily builds `DynamicModel` and computes the per-keyframe dynamic mask. All gated by
   `use_dynamic` ⇒ zero effect on the loop / KITTI / mesh runs.
4. **`scripts/run.py`** — full-mapping mode now writes the final (loop-corrected)
   trajectory to `<save_dir>/traj_final/<camera_timestamp>.txt` (the per-frame `droid_c2w`
   dump only happened in `frontend_only` mode). Needed for ATE eval of loop + long runs.
5. **`scripts/loop/loop_model.py`** — corrected-pose writer hardened with `.cpu()`
   (`...matrix().cpu().numpy()`) to avoid a CUDA→numpy crash when a loop fires.

> Dynamic Eraser interpretation note: the paper applies the eraser inside the frontend
> BA. The public code never wired the eraser into any loss; we integrate it into the
> Gaussian-mapping photometric loss (the only exposed mechanism). The qualitative
> "erased map" result is solid; the quantitative ATE on/off effect depends on how much
> the masked map feeds back into pose estimation — to be confirmed at run time.

## 3. Configs (in `configs/`, AutoDL paths baked in)

- `loop/kitti08_long.yaml` — seq08 (2011_09_30_drive_0028), full mapping, `use_loop: True`
  (seq08 has an internal revisit at frames 788↔1424), BEV vis on. mode `vo`.
- `loop/kitti07_loop_off.yaml` / `loop/kitti07_loop_on.yaml` — seq07
  (2011_09_30_drive_0027, data already staged), differ only in `use_loop`. seq07's end
  returns to its start (GT revisit 0.11 m) → loop fires.
- `dynamic/bonn_<seq>_{off,on}.yaml` — 4 seqs × on/off; mono + Metric3D depth;
  `_on` sets `use_dynamic: True`. Seqs: balloon, person_tracking, person_tracking2,
  moving_nonobstructing_box2 (= Table IV ball / ps tk / ps tk2 / mv box2).
- `mesh/waymo_scene13_mesh.yaml` — Scene13 (Scene01 not staged), `debug_mode: True` to
  dump per-frame depth+pose for TSDF fusion.

## 4. Helper scripts (`scripts/`)

- `eval_loop_compare.py` — `--off <dir> --on <dir> --seq 07` → ATE/t_rel table +
  GT/off/on trajectory overlay PNG. Also `--single <dir> --seq 08` for the long run.
- `eval_bonn.py` — `--table --results_root results/dynamic --bonn_root .../bonn` →
  Table IV (wo/with Eraser, cm). Sim(3)-aligned (monocular).
- `export_tsdf_mesh.py` — `--result <dir>` → Open3D TSDF mesh `.ply` from `debug_dict/`.

## 5. Data staging (server `/root/autodl-tmp/data/`)

- KITTI seq07: already present (1106 imgs + metadata).
- KITTI seq08 (drive_0028): the official sync zip is 21 GB (velodyne); only `image_02`
  (5177 png, 4.23 GB) is fetched via a single contiguous HTTP byte-range
  (`/root/carve_kitti08.py`, avoids S3 rate-limiting). Metadata copied from `KITTI_Sync`.
- BONN: 4 seqs downloaded to `bonn/rgbd_bonn_<seq>/`, `rgb/*.png` converted to
  `color/*.jpg` for the loader; `groundtruth.txt` kept for eval.

## 6. GPU run commands (run each in a `tmux` window)

```bash
source /root/miniconda3/etc/profile.d/conda.sh && conda activate vings_vio
R=/root/autodl-tmp/VINGS-Mono-SLAM-Course ; V=$R/third_party/VINGS-Mono
export LD_LIBRARY_PATH=/root/miniconda3/envs/vings_vio/lib/python3.9/site-packages/torch/lib:$LD_LIBRARY_PATH
export PYTHONPATH=$V/scripts:$V/scripts/frontend:$PYTHONPATH
cd $V/scripts

# (1) Loop on/off + long-trajectory on seq07 (data ready). The _off run also serves as
#     the KITTI long-trajectory mapping demo.
python run.py $R/configs/loop/kitti07_loop_off.yaml
python run.py $R/configs/loop/kitti07_loop_on.yaml
python $R/scripts/eval_loop_compare.py --seq 07 --out_dir $R/results/loop \
   --off $(ls -d $R/results/loop/*kitti07_loop_off*/ | tail -1) \
   --on  $(ls -d $R/results/loop/*kitti07_loop_on*/  | tail -1)

# (2) TSDF mesh (Waymo Scene13, data ready)
python run.py $R/configs/mesh/waymo_scene13_mesh.yaml
python $R/scripts/export_tsdf_mesh.py --depth pred --voxel 0.1 --trunc 0.4 --max_depth 40 \
   --result $(ls -d $R/results/loop/*waymo_scene13_mesh*/ | tail -1)

# (3) BONN Dynamic Eraser ablation — run after BONN download finishes (8 runs; _on uses FastSAM)
for cfg in $R/configs/dynamic/bonn_*.yaml; do echo "=== $cfg ==="; python run.py "$cfg"; done
python $R/scripts/eval_bonn.py --table --results_root $R/results/dynamic --bonn_root /root/autodl-tmp/data/bonn

# (4) OPTIONAL stretch: KITTI08 3.2 km — only if the seq08 carve (tmux 'seq08') completed
python run.py $R/configs/loop/kitti08_long.yaml
python $R/scripts/eval_loop_compare.py --single $(ls -d $R/results/loop/*kitti08_long*/ | tail -1) --seq 08
```

## 7. Verification / targets

- Each run finishes without OOM; `traj_final/` + `ply/*.ply` produced.
- Loop: console prints `Loop detected!`; loop-ON ATE < loop-OFF ATE (overlay PNG shows
  drift correction). Target: ≥1 loop triggered + complete KITTI08 run.
- BONN: `_on` ATE < `_off`; ball/balloon ATE ≤ ~8 cm (paper 4.08). Table IV reproduced as a trend.
- Mesh: non-empty `.ply`, continuous surface in Meshlab.

## 8. Risks / fallbacks

- Dynamic Eraser ATE effect uncertain (see §2 note) → fallback: qualitative erased-map
  figure/video; if VO map scale is unstable, tune `iters`/lr or use `gt` depth in eval.
- Loop may not trigger under heavy VO drift → lower `is_loop_min_match_num` /
  `is_loop_mse_threshold`, or try `mode: vio`.
- KITTI08 download blocked once by S3 throttling → solved via single-range carve.
- TSDF noisy → raise `--voxel`/`--trunc`, subsample with `--stride`.
