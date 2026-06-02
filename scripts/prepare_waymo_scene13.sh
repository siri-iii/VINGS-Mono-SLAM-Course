#!/usr/bin/env bash
set -euo pipefail

if [[ $# -ne 1 ]]; then
  echo "Usage: $0 segment-..._with_camera_labels" >&2
  echo "Scene13 is an author-local alias. Confirm its official Waymo segment id before running." >&2
  exit 2
fi

segment=${1%.tfrecord}
repo_root=$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)
neuralsim_root=${NEURALSIM_ROOT:-/root/autodl-tmp/person_b_external/neuralsim}
gsutil=${GSUTIL:-/root/autodl-tmp/person_b_external/google-cloud-sdk/bin/gsutil}
preprocess_python=${WAYMO_PREPROCESS_PYTHON:-/root/autodl-tmp/person_b_external/waymo_preprocess/bin/python}
data_root=${WAYMO_DATA_ROOT:-/root/autodl-tmp/data/waymo}
raw_root="$data_root/raw/training"
processed_root="$data_root/neuralsim_processed"
vings_root="$data_root/Waymo_Scene13"
raw_file="$raw_root/$segment.tfrecord"
seq_list="$data_root/scene13_segment.lst"
source="gs://waymo_open_dataset_v_1_4_2/individual_files/training/$segment.tfrecord"

[[ -x "$gsutil" ]] || { echo "Missing gsutil: $gsutil" >&2; exit 1; }
[[ -x "$preprocess_python" ]] || { echo "Missing preprocess Python: $preprocess_python" >&2; exit 1; }
[[ -f "$neuralsim_root/dataio/autonomous_driving/waymo/preprocess.py" ]] || { echo "Missing NeuralSim checkout: $neuralsim_root" >&2; exit 1; }
mkdir -p "$raw_root" "$processed_root" "$vings_root"
printf '%s\n' "$segment" > "$seq_list"

if [[ ! -s "$raw_file" ]]; then
  echo "Downloading authorized Waymo TFRecord: $source"
  "$gsutil" cp -n "$source" "$raw_root/"
fi

echo "Preprocessing with NeuralSim"
(
  cd "$neuralsim_root"
  vings_site=/root/miniconda3/envs/vings_vio/lib/python3.9/site-packages
  PYTHONPATH="$neuralsim_root:$neuralsim_root/nr3d_lib:$vings_site${PYTHONPATH:+:$PYTHONPATH}" "$preprocess_python" \
    dataio/autonomous_driving/waymo/preprocess.py \
    --root "$raw_root" --out_root "$processed_root" --seq_list "$seq_list" -j1
)

echo "Exporting VINGS-Mono color/pose layout"
python "$repo_root/scripts/export_neuralsim_waymo_to_vings.py" \
  "$processed_root/$segment" "$vings_root" --force

echo "Ready: $vings_root"
