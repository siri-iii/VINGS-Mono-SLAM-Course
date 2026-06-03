# Person C — Frontend Dynamic Eraser (attempt to reproduce BONN Table IV)

Goal: make the Dynamic Eraser affect the **trajectory** (not just the map), so the BONN
on/off ATE actually diverges toward the paper. Implemented offline (server was down);
**needs validation on the GPU server** before trusting the numbers.

## Why the first attempt didn't reproduce Table IV
Our earlier integration masked dynamic pixels in the **Gaussian mapping loss** → cleans the
map but leaves the **DROID frontend BA** (which produces the poses) untouched → on/off ATE
was noise-level. The paper masks in the frontend BA. This change does that.

## What was implemented (4 parts)

1. **`scripts/gen_dynamic_masks.py`** (new) — precompute per-frame dynamic masks:
   FastSAM everything-segmentation + Farneback optical flow; a segment is dynamic if its
   median flow ≫ background (camera-induced) flow. Saves `<root>/dynamic_masks/<i>.npy` at
   H/8×W/8 (the frontend feature resolution) + optional viz overlays.

2. **Frontend BA injection** — `scripts/_personC_patches/frontend_eraser_depth_video.patch`
   (full patched file alongside as `depth_video.py.patched`). In `DepthVideo`:
   - new buffer `self.dynamic_mask` (buffer, H/8, W/8) + flags `use_dynamic_frontend`,
     `dynamic_mask_dir` from cfg;
   - on keyframe append (`__item_setter`) load that frame's mask;
   - in `ba()` multiply the per-edge confidence `weight` by `(1 − dynamic_mask[ii])` so
     dynamic correspondences don't constrain pose/depth.
   - **Fully guarded**: default `use_dynamic_frontend: False` ⇒ zero effect on all existing
     runs (loop/KITTI/mesh). Shape-checked: silently no-ops if the weight layout differs.

3. **BONN configs** (`configs/dynamic/bonn_*.yaml`):
   - `_on` now sets `use_dynamic_frontend: True` + `dynamic_mask_dir: <root>/dynamic_masks`;
   - all 8 relax keyframe selection for slow indoor mono: `filter_thresh 2.4→1.2`,
     `keyframe_thresh 4.0→2.0`, `translation_threshold 0.3→0.1` (fixes the 3–17-keyframe problem).

4. **Per-frame eval** — `eval_bonn.py --interp` interpolates keyframe poses to every GT
   timestamp before Sim(3)+ATE (closer to the paper's dense protocol).

## How to apply + run on the server (when it is back)

```bash
R=/root/autodl-tmp/VINGS-Mono-SLAM-Course ; V=$R/third_party/VINGS-Mono
# 1) sync the main-repo changes (scripts/configs/docs) -- pull or scp from local
# 2) apply the frontend patch to the submodule
cp $V/scripts/frontend/depth_video.py $V/scripts/frontend/depth_video.py.bak_preeraser
git -C $V apply $R/scripts/_personC_patches/frontend_eraser_depth_video.patch \
  || cp $R/scripts/_personC_patches/depth_video.py.patched $V/scripts/frontend/depth_video.py
python -c "import ast; ast.parse(open('$V/scripts/frontend/depth_video.py').read()); print('parse ok')"

source /root/run_env.sh
# 3) precompute dynamic masks for each BONN seq (H/8=48, W/8=64 for image_size [384,512])
for s in balloon person_tracking person_tracking2 moving_nonobstructing_box2; do
  python $R/scripts/gen_dynamic_masks.py --root /root/autodl-tmp/data/bonn/rgbd_bonn_$s \
    --pattern 'color/*.jpg' --h8 48 --w8 64 --viz
done
# 4) re-run BONN on/off, then eval per-frame
for cfg in $R/configs/dynamic/bonn_*.yaml; do python run.py "$cfg"; done
python $R/scripts/eval_bonn.py --table --results_root $R/results/dynamic \
       --bonn_root /root/autodl-tmp/data/bonn --interp
```

## Validation checklist (first thing to confirm on the server)
- `depth_video.py` parses & a normal run (use_dynamic_frontend off) is unchanged.
- A masked run prints no `[dynamic_eraser] weight masking skip:` (means the weight/mask
  shapes matched — the down-weighting is actually happening). If it *does* print skip,
  inspect the real `weight` shape at `ba()` and adjust `_apply_dynamic_weight`.
- `dynamic_masks_viz/*.png` highlight the people/boxes (mask quality sanity check).
- BONN `_on` keyframe count is now tens–hundreds (not 3–17).
- Compare `_on` vs `_off` ATE: expect `_on` clearly lower on person_tracking / balloon.

## Honest expectations
- This is the **correct place** to mask, so on/off should now diverge meaningfully.
- Hitting the exact paper numbers (~4 cm) is still gated by the **frontend accuracy ceiling**
  (A's finding: the public frontend underperforms the paper, no official recipe) and by the
  quality of our flow-based dynamic detection. Target: a clear, defensible on<off improvement,
  not necessarily 4.08 cm exactly.
- The `weight`-shape assumption in `_apply_dynamic_weight` is the one untested risk; it's
  guarded to fail safe, but confirm it's actually applying (see checklist).
