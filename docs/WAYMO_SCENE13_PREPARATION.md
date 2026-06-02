# Waymo Scene13 Preparation

Updated: 2026-05-31

## Prepared Server State

The NeuralSim-based Waymo staging pipeline is installed and validated up to the external authorization boundary.

| Component | Path |
| --- | --- |
| Official NeuralSim checkout | `/root/autodl-tmp/person_b_external/neuralsim` |
| NeuralSim `nr3d_lib` fixed-commit source | `/root/autodl-tmp/person_b_external/neuralsim/nr3d_lib` |
| Google Cloud SDK `526.0.0` | `/root/autodl-tmp/person_b_external/google-cloud-sdk` |
| Isolated TensorFlow/Waymo preprocess env | `/root/autodl-tmp/person_b_external/waymo_preprocess` |
| Raw TFRecord directory | `/root/autodl-tmp/data/waymo/raw/training` |
| NeuralSim processed directory | `/root/autodl-tmp/data/waymo/neuralsim_processed` |
| Final VINGS Scene13 directory | `/root/autodl-tmp/data/waymo/Waymo_Scene13` |

Verified imports: TensorFlow `2.11.0`, Waymo devkit `waymo-open-dataset-tf-2-11-0==1.5.2`, NumPy `1.21.5`. NeuralSim `preprocess.py --help` also runs successfully.

## Required External Inputs

1. Accept the Waymo Open Dataset Terms of Use at `https://waymo.com/open/`.
2. Authenticate the installed Google Cloud CLI interactively:

```bash
/root/autodl-tmp/person_b_external/google-cloud-sdk/bin/gcloud auth login --no-launch-browser
```

Open the printed URL locally, complete Google login, and paste the verification code back into the remote prompt.

3. Confirm the official Waymo `segment-*` id corresponding to the VINGS author-local alias `Waymo_Scene13`. This mapping is not published in the VINGS repository and must not be guessed from list order.

## Run Preparation

After authentication and segment confirmation:

```bash
cd /root/autodl-tmp/VINGS-Mono-SLAM-Course
./scripts/prepare_waymo_scene13.sh segment-..._with_camera_labels
```

The adapted VINGS config is `configs/waymo/scene13.yaml`. The script downloads the authorized v1.4.2 training TFRecord, runs the official NeuralSim preprocessor with one worker, then exports `camera_FRONT` data into:

```text
/root/autodl-tmp/data/waymo/Waymo_Scene13/
├── SOURCE_SEGMENT.txt
├── color/
│   └── 00000.jpg
└── pose/
    └── 00000.txt
```

Images are symlinked from the NeuralSim processed output to avoid duplicate storage. Poses are exported from `scenario.pt -> observers -> camera_FRONT -> data -> c2w`.

## Validation Evidence

- Official bucket network probe reaches Google Cloud Storage but currently returns `401 Anonymous caller`, confirming that the remaining download blocker is authentication.
- `scripts/export_neuralsim_waymo_to_vings.py` passed a synthetic three-frame smoke test.
- `scripts/prepare_waymo_scene13.sh` passes `bash -n`.

## Candidate Mapping

Inference only: VINGS publishes configs named `Scene01`, `Scene03`, `Scene07`, `Scene13`, `Scene14`, `Scene15`, and `Scene32`, while NeuralSim publishes `waymo_static_32.lst`. If VINGS numbering follows that list, the Scene13 candidate is its 13th line:

```text
segment-16608525782988721413_100_000_120_000_with_camera_labels
```

The candidate is staged at `/root/autodl-tmp/data/waymo/scene13_candidate_segment.lst`. Confirm it before downloading because the VINGS repository does not publish the mapping explicitly.
