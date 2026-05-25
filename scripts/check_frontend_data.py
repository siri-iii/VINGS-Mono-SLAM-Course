"""Check whether datasets required by Person A frontend tasks are staged."""
import argparse
import os
from pathlib import Path

KITTI_ROOT = Path("/root/autodl-tmp/data/kitti_raw/2011_09_30/2011_09_30_drive_0027_sync")
KITTI_GT = Path("/root/autodl-tmp/data/kitti_gt/dataset/poses/07.txt")
WAYMO_ROOT = Path("/root/autodl-tmp/data/waymo/Scene01")


def count_files(path, suffix):
    if not path.exists():
        return 0
    return sum(1 for _ in path.glob(f"*{suffix}"))


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--waymo_root", default=str(WAYMO_ROOT))
    args = parser.parse_args()
    waymo_root = Path(args.waymo_root)

    checks = []
    checks.append(("KITTI raw", KITTI_ROOT.exists(), str(KITTI_ROOT)))
    checks.append(("KITTI camstamp", (KITTI_ROOT / "metadata" / "camstamp.txt").exists(), str(KITTI_ROOT / "metadata" / "camstamp.txt")))
    checks.append(("KITTI GT", KITTI_GT.exists(), str(KITTI_GT)))
    checks.append(("Waymo root", waymo_root.exists(), str(waymo_root)))
    checks.append(("Waymo color", count_files(waymo_root / "color", ".jpg") > 0, str(waymo_root / "color")))
    checks.append(("Waymo pose", count_files(waymo_root / "pose", ".txt") > 0, str(waymo_root / "pose")))

    ok = True
    for name, passed, evidence in checks:
        ok = ok and passed
        print(f"{name:14s}: {'OK' if passed else 'MISSING'}  {evidence}")
    if not ok:
        raise SystemExit(2)


if __name__ == "__main__":
    main()
