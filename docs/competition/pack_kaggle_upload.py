#!/usr/bin/env python3
"""Create Kaggle upload zip bundles from docs/competition/output/."""

from __future__ import annotations

import argparse
import zipfile
from pathlib import Path

COMPETITION_ROOT = Path(__file__).resolve().parent
OUTPUT_DIR = COMPETITION_ROOT / "output"

PUBLIC_FILES = (
    "train.csv",
    "test.csv",
    "sample_submission.csv",
    "id_game_map.csv",
    "data_dictionary.md",
    "competition_description.md",
)

HOST_FILES = ("solution.csv",)


def _zip_files(archive_path: Path, files: tuple[str, ...], *, root: Path) -> None:
    missing = [name for name in files if not (root / name).exists()]
    if missing:
        raise FileNotFoundError(f"Missing files for {archive_path.name}: {missing}")

    archive_path.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(archive_path, "w", compression=zipfile.ZIP_DEFLATED) as zf:
        for name in files:
            zf.write(root / name, arcname=name)


def main() -> int:
    parser = argparse.ArgumentParser(description="Pack Kaggle public + host zip files.")
    parser.add_argument("--output-dir", default=str(OUTPUT_DIR))
    args = parser.parse_args()
    root = Path(args.output_dir)

    public_zip = root / "chesstrainer_kaggle_public.zip"
    host_zip = root / "chesstrainer_kaggle_host_solution.zip"

    _zip_files(public_zip, PUBLIC_FILES, root=root)
    _zip_files(host_zip, HOST_FILES, root=root)

    print(f"Public bundle:  {public_zip} ({public_zip.stat().st_size / 1_048_576:.1f} MB)")
    print(f"Host bundle:    {host_zip} ({host_zip.stat().st_size / 1_048_576:.2f} MB)")
    print("\nUpload public zip as Kaggle Dataset.")
    print("Upload host zip only in competition admin (solution / answer key).")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
