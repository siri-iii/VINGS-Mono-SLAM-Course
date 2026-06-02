# Person B External Blockers

Updated: 2026-05-31

## Missing Authorized Datasets

| Requirement | Missing path on server | Evidence | Resolution |
| --- | --- | --- | --- |
| B6 ScanNet-0106 ablation | `/root/autodl-tmp/data/scannet/...` | No ScanNet directory under `/root/autodl-tmp/data`; public upstream dataset listing does not include ScanNet | Provision an authorized extracted ScanNet scene and adapt a local config |
| B6 Waymo-Scene13 ablation | `/root/autodl-tmp/data/waymo/Waymo_Scene13` | NeuralSim pipeline is installed; bucket probe returns `401 Anonymous caller` | Authenticate Waymo access and provide the official `segment-*` id mapped to author-local alias Scene13 |
| B8 strict 3x3 ATE table | Original three GT scenes | Required GT data is absent | Stage all requested scenes with `pose/*.txt`, then run `scripts/eval_pose_dir.py` for each result |

The public project dataset page is `https://huggingface.co/datasets/Promethe-us/VINGS-Mono-Dataset/tree/main`. Upstream data preparation notes are at `https://github.com/Fudan-MAGIC-Lab/VINGS-Mono/blob/main/docs/PREPARE_DATA.md`.

The server also cannot directly reach the Hugging Face API (`Errno 101: Network is unreachable`), so authorized archives must be staged through an available transfer route.

## Completed Local Replacements

- B6: five-threshold Hotel fallback Score Manager table.
- B7: official-source isolated builds and synthetic profiling for Sample, Original 2DGS, and Taming3DGS rasterizers.
- B8: selectable pose-refinement strategies on a Hotel subset plus reusable Sim(3) ATE evaluation; SmallCity baseline ATE recorded.
- B10: strict SmallCity BEV trajectory recording generated from saved keyframes and GT alignment.

Waymo staging commands and validated server paths are documented in `docs/WAYMO_SCENE13_PREPARATION.md`.
