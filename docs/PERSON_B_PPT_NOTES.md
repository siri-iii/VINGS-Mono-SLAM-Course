# Person B PPT Notes: 2D Gaussian Mapping

Updated: 2026-05-31

## Page 1: Online Mapping Pipeline

- Input tracking frames and depth estimates are incrementally converted into 2D Gaussians.
- Mapping alternates Gaussian optimization, densification, pruning, and pose-aware updates.
- Demo evidence: Hotel completed 405 frames; Hierarchical-SmallCity completed 877 frames.
- Visual: `media/figures/smallcity_bev_final_person_b.png`

## Page 2: Score Manager

- Hotel fallback threshold `0.8` reduces final Gaussian count from 1,375,682 to 1,038,274 while PSNR remains 32.887 to 32.952.
- Higher thresholds reduce count further but quality is scene-dependent; threshold `25.6` drops to 28.759 PSNR.
- State clearly that ScanNet-0106 and Waymo-Scene13 require externally provisioned authorized data.

## Page 3: Rasterizer Comparison

- Unified RTX 4090 synthetic profile: 200k Gaussians, 344x616, 20 iterations, RGB mean loss.
- Total mean: Sample Rasterizer `6.769 ms`, Original 2DGS `6.841 ms`, Taming3DGS rasterizer branch `1.318 ms`.
- Clarify that Taming3DGS uses a 3DGS scale contract and does not emit 2DGS depth, so this is kernel timing rather than end-to-end quality equivalence.

## Page 4: Pose Refinement and BEV Recording

- Hotel fallback final PSNR: `v1` 22.365, `v2` 25.676, `curpose` 22.859; all runs exit `0`.
- Sim(3)-aligned SmallCity baseline ATE: `4.144531 m` across 317 matched keyframes.
- Play strict BEV recording: `media/videos/smallcity_bev_mapping_person_b_2min.mp4` (`317` frames, `119.985` seconds, `960x960`).
