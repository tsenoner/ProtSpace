#!/usr/bin/env python3
"""Script to run protspace-json on multiple similarity matrices."""

from pathlib import Path
import subprocess
from typing import Dict

# Configuration
BASE_PATH = Path("data/gfp/processed_data")
OUTPUT_FILE = Path("data/gfp/protspace/gfp.json")
METADATA_FILE = BASE_PATH / "gfp_features.csv"

# Input matrices with their name prefixes
MATRICES = {
    "prott5_subset_1000.h5": "prott5",
    "sequence_fident_matrix.csv": "seq_fident",
    "structure_alntmscore_matrix.csv": "struct_aln",
    "structure_bits_matrix.csv": "struct_bits",
    "structure_evalue_matrix.csv": "struct_eval",
    "structure_fident_matrix.csv": "struct_fident",
    "structure_lddt_matrix.csv": "struct_lddt",
    "structure_rmsd_matrix.csv": "struct_rmsd",
}

# Methods to run for each matrix
METHODS = ["umap2", "mds2"]

def create_protspace_command(
    input_file: Path,
    custom_names: Dict[str, str]
) -> str:
    """Create a protspace-json command with the given parameters."""
    methods_str = " ".join(custom_names)
    names_str = " ".join(f"{k}={v}" for k, v in custom_names.items())

    return (
        f"uv run protspace-json "
        f"-i {input_file} "
        f"-m {METADATA_FILE} "
        f"-o {OUTPUT_FILE} "
        f"--methods {methods_str} "
        f"--custom_names {names_str}"
    )

def main():
    """Run protspace-json for all matrices with all methods."""
    for matrix_file, prefix in MATRICES.items():
        input_file = BASE_PATH / matrix_file
        print(f"\nProcessing matrix: {matrix_file}")

        # Create custom names using the matrix prefix
        custom_names = {method: f"{prefix}_{method}" for method in METHODS}

        cmd = create_protspace_command(input_file, custom_names)
        print(f"Running: {cmd}")
        subprocess.run(cmd, shell=True, check=True)

if __name__ == "__main__":
    main()