#!/bin/bash
set -euo pipefail
TORCH_LIB=/root/miniconda3/envs/vings_vio/lib/python3.9/site-packages/torch/lib
SCRIPTS=/root/autodl-tmp/VINGS-Mono-SLAM-Course/third_party/VINGS-Mono/scripts
REPO=/root/autodl-tmp/VINGS-Mono-SLAM-Course
export LD_LIBRARY_PATH=$TORCH_LIB:${LD_LIBRARY_PATH:-}
export PYTHONPATH=$SCRIPTS:$SCRIPTS/frontend:${PYTHONPATH:-}
cd "$REPO"
python scripts/check_frontend_data.py
cd "$SCRIPTS"
/root/miniconda3/envs/vings_vio/bin/python run.py "$REPO/configs/waymo/waymo01.yaml" 2>&1 | tee /root/waymo01_vo.log
