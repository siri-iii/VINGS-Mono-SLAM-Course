# Person B: 2D Gaussian Mapping Reproduction and Ablation

Updated: 2026-06-02

## Scope and Reproduction Boundary

Person B completed the runnable mapping package on the server data. Waymo Scene13 data was downloaded and processed (2026-06-02): official TFRecord from gs://waymo_open_dataset_v_1_4_3, 198 camera_FRONT frames exported. B6 has been completed on Scene13. ScanNet-0106 remains externally blocked.

## Main Demo Results

| Demo | Frames | Status | Final map |
| --- | ---: | --- | --- |
| Hotel | 405 | Completed, exit 0 | `results/hotel/05-28-21-38-rtgslam-hote-_personB_full/ply/idx=404_2dgs.ply` |
| Hierarchical-SmallCity | 877 | Completed, exit 0 | `results/mapping/smallcity/05-28-22-09-hierarchical-smallcit-_personB_full_looperfix/ply/idx=876_2dgs.ply` |

SmallCity presentation assets:

- Strict 2-minute BEV trajectory recording: `media/videos/smallcity_bev_mapping_person_b_2min.mp4`
- Strict BEV final frame: `media/figures/smallcity_bev_final_person_b.png`
- Supplemental RGB/depth/normal visualization: `media/videos/smallcity_mapping_person_b_2min.mp4`

## B6: Score Manager Ablation

The configurable value is `score_manager.prune_importance_upper`.

Waymo Scene13 results (198 frames, 2026-06-02):

| Upper threshold | Final Gaussians | Final PSNR |
| ---: | ---: | ---: |
| 0 | 1,332,583 | 21.052 |
| **0.8 (paper default)** | **1,211,279** | **24.620** |
| 12.8 | 1,199,918 | 24.297 |
| 25.6 | 1,206,088 | 21.816 |
| 102.4 | 1,201,694 | 20.281 |

Threshold 0.8 achieves the highest PSNR (+3.6 dB over threshold 0) while reducing Gaussian count by 9.1%. Thresholds above 12.8 degrade quality, consistent with the paper default. Hotel fallback reference: `results/mapping/person_b/summaries/score_manager_hotel_fallback.csv`

Scene13 summary CSV: `results/mapping/person_b/summaries/score_manager_scene13.csv`

## B7: Rasterizer Profiling

Official source variants were compiled in isolated external directories with the `vings_vio` CUDA 11.8 toolchain:

- Sample Rasterizer: checked-out `Promethe-us/diff-surfel-rasterization` fork.
- Original 2DGS: `hbb1/diff-surfel-rasterization`.
- Taming3DGS: `humansensinglab/taming-3dgs`, `rasterizer` branch.

Unified profile: RTX 4090, 200,000 points, 344x616, 3 warmups, 20 measured iterations, RGB mean loss.

| Implementation | Scale dimensions | Depth output | Backward mean | Total mean |
| --- | ---: | --- | ---: | ---: |
| Sample Rasterizer | 2 | Yes | 5.171 ms | 6.769 ms |
| Original 2DGS | 2 | Yes | 5.708 ms | 6.841 ms |
| Taming3DGS rasterizer branch | 3 | No | 0.832 ms | 1.318 ms |

Taming3DGS is not a drop-in quality comparison for this mapping pipeline: it uses the 3DGS scale contract and does not emit the 2DGS depth map. The table is a synthetic kernel timing comparison only. End-to-end PSNR is intentionally not claimed.

Summary CSV: `results/mapping/person_b/summaries/rasterizer_profile_20260531.csv`

## B8: Pose Refinement Ablation

The renderer now selects `pose_refine_strategy` as `v1`, `v2`, or `curpose`. A stale renderer branch was removed because it double-transformed world-space points and passed `rotations=None` without precomputed covariance.

| Strategy | Scene | Frames | Final Gaussians | Final PSNR | ATE |
| --- | --- | ---: | ---: | ---: | --- |
| `v1` | Hotel fallback subset | 120 | 579,116 | 22.364601 | GT unavailable |
| `v2` | Hotel fallback subset | 120 | 576,366 | 25.676336 | GT unavailable |
| `curpose` | Hotel fallback subset | 120 | 577,945 | 22.858814 | GT unavailable |

All three fallback runs exited `0`. A reusable Sim(3)-aligned evaluator was added as `scripts/eval_pose_dir.py`. On the existing full SmallCity baseline output it matches 317 saved keyframes against GT and reports `ATE RMSE = 4.144531 m` and median error `2.397249 m`.

The strict three-strategy by three-scene ATE table remains externally blocked because the requested three GT datasets are not available on this server.

## Runtime Notes

- Use conda environment `vings_vio`, not `base`.
- For extension rebuilds use `CUDA_HOME=/root/miniconda3/envs/vings_vio`; it contains CUDA 11.8 matching PyTorch `2.0.1+cu118`.
- Raw logs are under `results/mapping/person_b/logs/`.
- Adapted configs are under `configs/ablations/person_b/`.
- External blocker details: `docs/PERSON_B_BLOCKERS.md`.
