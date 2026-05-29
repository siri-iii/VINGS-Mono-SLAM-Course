# Person B Execution Plan

Updated: 2026-05-28
Owner: Person B
Task package: 2D Gaussian Mapping Core

## Objective

Complete Person B's 2D Gaussian mapping task package for the SLAM final project, including demo reproduction, ablation experiments, result organization, and presentation-ready materials.

## Scope

Person B is responsible for:

- Core modules: Score Manager, Sample Rasterizer, Pose Refinement
- Main demos: Hotel demo and Hierarchical-SmallCity demo
- Ablations: Score Manager, Sample Rasterizer profiling, Pose Refinement
- Deliverables: `docs/ABLATION.md`, `results/mapping/`, and one 2-minute SmallCity BEV mapping recording
- PPT topic: 2D Gaussian Mapping: score management, sampled rasterization, and multi-frame pose optimization

## Execution Principles

- Verify the environment before running long experiments.
- Save every important command, config, log path, and output path.
- Keep algorithm changes minimal. Only fix paths, dependency issues, or compatibility problems when necessary.
- If an official dataset, checkpoint, config, or implementation is missing, record the blocker and use a clearly documented fallback.
- Update `docs/PERSON_B_PROGRESS.md` after each completed task.

## Phase 1: Verify Server and Repository State

Tasks:

- Enter the remote server and locate the project repository.
- Check the current git status and branch.
- Check whether `third_party/VINGS-Mono` is present and initialized.
- Check CUDA, NVIDIA driver, conda environment, Python, PyTorch, and CUDA extension status.
- Confirm whether the environment prepared by Person A is usable.

Expected output:

- Environment summary in the progress document.
- Any missing dependency or path issue recorded before experiments begin.

## Phase 2: Locate Person B Entrypoints

Tasks:

- Inspect the project README and reproduction plan.
- Inspect VINGS-Mono config files under `configs/`.
- Locate Hotel and Hierarchical-SmallCity configs.
- Locate mapping-related scripts and command-line entrypoints.
- Identify output directories, log conventions, and result file formats.

Expected output:

- A list of confirmed commands or candidate commands for the B experiments.
- A list of configs and datasets required by each experiment.

## Phase 3: Run a Minimal Environment Smoke Test

Tasks:

- Run a short demo or low-cost command first.
- Verify model loading, dataset access, CUDA availability, rasterizer imports, and output writing.
- Fix environment issues before launching long runs.

Expected output:

- Smoke test command, log path, and result status.
- Any fixes applied during setup.

## Phase 4: Run Main Demo Experiments

Tasks:

- Run Hotel demo.
- Run Hierarchical-SmallCity demo.
- Save logs, output directories, rendered images, trajectory files, BEV screenshots, and available video material.

Expected output:

- Demo result summary.
- Output paths under `results/mapping/` or the repository's native output directory.
- Candidate material for the 2-minute SmallCity BEV recording.

## Phase 5: Score Manager Ablation

Tasks:

- Run threshold settings: `0`, `0.8`, `12.8`, `25.6`, `102.4`.
- Target scenes: ScanNet-0106 and Waymo-Scene13, if data and configs are available.
- Record Gaussian count and PSNR for each setting.

Expected output:

- Score Manager ablation table.
- Logs and configs for each run.
- Notes for any unavailable dataset/config.

## Phase 6: Sample Rasterizer Profiling

Tasks:

- Compare available rasterization/backpropagation strategies:
  - Original 2DGS
  - Taming3DGS
  - Sample Rasterizer
- Record backward time, total time, and PSNR.
- If not all strategies are implemented in this codebase, document what is reproducible and what is missing.

Expected output:

- Profiling table.
- Exact commands and timing logs.
- Clear notes on implementation availability.

## Phase 7: Pose Refinement Ablation

Tasks:

- Run 3 pose refinement strategies across 3 scenes, for up to 9 experiments.
- Record ATE, PSNR, convergence behavior, and failure cases as available from the code outputs.

Expected output:

- Pose Refinement ablation table.
- Logs and output directories for all successful runs.
- Blocker notes for unavailable settings.

## Phase 8: Organize Deliverables

Tasks:

- Create or update `docs/ABLATION.md`.
- Create or update `results/mapping/`.
- Collect key commands, configs, logs, figures, tables, and screenshots.
- Keep raw logs separate from summarized results.

Expected output:

- A clean result directory for Person B.
- A readable ablation document ready for report integration.

## Phase 9: Prepare Presentation Material

Tasks:

- Prepare content for approximately four PPT pages:
  - Online mapping pipeline
  - Score Manager
  - Sample Rasterizer
  - Pose Refinement and ablation results
- Prepare or identify SmallCity BEV mapping recording material.

Expected output:

- PPT-ready bullet points and figures.
- Video or recording source path for the SmallCity BEV mapping process.
