#!/usr/bin/env python3
"""Download veekun CSV data from GitHub into python/assets/veekun-csv/."""

import os
import shutil
import subprocess
import sys
import tempfile

REPO_URL = "https://github.com/veekun/pokedex.git"
CSV_SUBDIR = "pokedex/data/csv"
OUTPUT_DIR = os.path.join("python", "assets", "veekun-csv")


def main():
    project_root = os.path.dirname(os.path.abspath(__file__))
    output_path = os.path.join(project_root, OUTPUT_DIR)

    print(f"Downloading veekun CSV data from {REPO_URL}")

    with tempfile.TemporaryDirectory() as tmp:
        clone_dir = os.path.join(tmp, "pokedex")

        # Shallow clone with sparse checkout — only fetches the CSV directory
        subprocess.run(
            ["git", "clone", "--depth", "1", "--filter=blob:none", "--sparse", REPO_URL, clone_dir],
            check=True,
        )
        subprocess.run(
            ["git", "-C", clone_dir, "sparse-checkout", "set", CSV_SUBDIR],
            check=True,
        )

        src = os.path.join(clone_dir, CSV_SUBDIR)
        csv_files = [f for f in os.listdir(src) if f.endswith(".csv")]
        if not csv_files:
            print("Error: no CSV files found in cloned repo", file=sys.stderr)
            sys.exit(1)

        os.makedirs(output_path, exist_ok=True)

        # Clear existing CSVs so removed upstream files don't linger
        for f in os.listdir(output_path):
            if f.endswith(".csv"):
                os.remove(os.path.join(output_path, f))

        for f in sorted(csv_files):
            shutil.copy2(os.path.join(src, f), output_path)

        print(f"Copied {len(csv_files)} CSV files to {OUTPUT_DIR}/")


if __name__ == "__main__":
    main()
