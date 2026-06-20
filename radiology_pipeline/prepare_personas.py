"""
prepare_personas.py
────────────────────────────────────────────────────────────────
Step 1 of the Radiology Digital Twin pipeline.

Takes persona .txt files produced by RadPersona (the Streamlit converter)
and renames them to the pid_XXXX.txt format expected by the upstream
Digital-Twin-Simulation pipeline.

Also writes a mapping CSV so you can trace every pid back to the original
file (and, if you have one, back to the anonymization key).

Usage
─────
    python radiology_pipeline/prepare_personas.py \
        --input_dir  path/to/unzipped/personas \
        --output_dir text_simulation/text_personas \
        --mapping_csv radiology_pipeline/pid_mapping.csv
"""

import os
import re
import shutil
import csv
import argparse
from pathlib import Path


def sanitize_pid(raw_name: str) -> str:
    """
    Accept any of the ID formats RadPersona produces and normalise to
    a plain integer string (for zero-padding).

    Supported formats: PT-001, P001, RDL-001, PAT-001, PT001, etc.
    Falls back to the raw filename stem if no number is found.
    """
    m = re.search(r"(\d+)", raw_name)
    return m.group(1) if m else raw_name


def prepare_personas(input_dir: str, output_dir: str, mapping_csv: str,
                     start_index: int = 1) -> int:
    """
    Copy persona .txt files to output_dir with pid_XXXX.txt naming.

    Returns the number of files processed.
    """
    input_path  = Path(input_dir)
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)

    txt_files = sorted(input_path.glob("*.txt"))
    if not txt_files:
        # Also search one level deep (unzipped zip may have a 'personas/' sub-folder)
        txt_files = sorted(input_path.rglob("*.txt"))

    if not txt_files:
        print(f"[prepare_personas] No .txt files found in {input_dir}")
        return 0

    mapping_rows = []
    pid_counter  = start_index

    for src in txt_files:
        raw_num = sanitize_pid(src.stem)
        try:
            n = int(raw_num)
        except ValueError:
            n = pid_counter   # fallback: sequential

        pid      = f"pid_{n:04d}"
        dst_name = f"{pid}.txt"
        dst      = output_path / dst_name

        shutil.copy2(src, dst)

        mapping_rows.append({
            "pid":           pid,
            "original_file": src.name,
            "original_stem": src.stem,
            "source_dir":    str(input_path.resolve()),
        })
        pid_counter += 1

    # Write mapping CSV
    mapping_path = Path(mapping_csv)
    mapping_path.parent.mkdir(parents=True, exist_ok=True)
    with open(mapping_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=["pid", "original_file",
                                               "original_stem", "source_dir"])
        writer.writeheader()
        writer.writerows(mapping_rows)

    print(f"[prepare_personas] Copied {len(mapping_rows)} persona files → {output_dir}")
    print(f"[prepare_personas] PID mapping saved  → {mapping_csv}")
    return len(mapping_rows)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Rename RadPersona output files to pid_XXXX format."
    )
    parser.add_argument(
        "--input_dir", required=True,
        help="Folder containing .txt persona files from RadPersona."
    )
    parser.add_argument(
        "--output_dir",
        default="text_simulation/text_personas",
        help="Destination folder (default: text_simulation/text_personas)."
    )
    parser.add_argument(
        "--mapping_csv",
        default="radiology_pipeline/pid_mapping.csv",
        help="Path for the PID-to-original-file mapping CSV."
    )
    parser.add_argument(
        "--start_index", type=int, default=1,
        help="Starting integer for pid numbering (default: 1)."
    )
    args = parser.parse_args()
    prepare_personas(args.input_dir, args.output_dir,
                     args.mapping_csv, args.start_index)
