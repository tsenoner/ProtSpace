from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd
from scipy.sparse import coo_matrix


def process_similarity_values(
    values: pd.Series, metric: str
) -> pd.Series:
    """Processes similarity values based on their meaning."""
    if metric == "evalue":
         # Convert evalues to similarities: -log10(evalue)
        processed = -np.log10(values.replace(0, 1e-300))
    elif metric == "bits":
        # Higher bits scores indicate better alignment
        processed = values
    elif metric == "rmsd":
        # Invert and scale RMSD: smaller RMSD = higher similarity
        max_rmsd = values.max()
        processed = (max_rmsd - values) / max_rmsd
        print(f"RMSD range after processing: {processed.min()} to {processed.max()}")
    else:
        processed = values

    if processed.min() != processed.max():
        processed = (processed - processed.min()) / (
            processed.max() - processed.min()
        )
    return processed.round(3)


def create_similarity_matrices(
    df: pd.DataFrame,
    columns: list[str],
    output_dir: Path,
) -> dict[str, pd.DataFrame]:
    """Creates similarity matrices from sequence comparison data."""
    output_dir.mkdir(parents=True, exist_ok=True)

    all_seqs = sorted(set(df["query"].unique()) | set(df["target"].unique()))
    seq_to_idx = {seq: idx for idx, seq in enumerate(all_seqs)}

    row_idx = np.array([seq_to_idx[seq] for seq in df["query"]])
    col_idx = np.array([seq_to_idx[seq] for seq in df["target"]])

    matrices = {}
    n_seqs = len(all_seqs)

    for col in columns:
        print(f"Processing {col} matrix...")

        if col == "rmsd":
            print(f"Number of RMSD values: {len(df[col])}")
            print(f"Number of non-zero RMSD: {(df[col] > 0).sum()}")

        processed_values = process_similarity_values(df[col], col)

        sparse_matrix = coo_matrix(
            (processed_values, (row_idx, col_idx)),
            shape=(n_seqs, n_seqs),
            dtype=np.float64,
        )
        matrix = sparse_matrix.toarray()
        np.fill_diagonal(matrix, 1.0)

        matrix_df = pd.DataFrame(
            matrix,
            index=all_seqs,
            columns=all_seqs,
        )

        matrix_df.to_csv(output_dir / f"structure_{col}_matrix.csv")
        matrices[col] = matrix_df

    return matrices


def main() -> dict[str, Any]:
    script_dir = Path(__file__).parent
    foldseek_result = (
        script_dir / "../foldseek_pdb_subset_1000/results.tsv"
    ).resolve()
    output_dir = (script_dir / "../processed_data").resolve()

    print("Reading input data...")
    df = pd.read_csv(foldseek_result, sep="\t")

    for column in ["query", "target"]:
        df[column] = df[column].str.replace("_", ":")

    columns = ["fident", "evalue", "bits", "lddt", "alntmscore", "rmsd"]

    missing_columns = [col for col in columns if col not in df.columns]
    if missing_columns:
        raise ValueError(f"Missing columns in input data: {missing_columns}")

    print("\nGenerating similarity matrices...")
    similarity_matrices = create_similarity_matrices(df, columns, output_dir)

    print("\nAll matrices generated successfully!")
    print(f"Output files can be found in: {output_dir}")

    return similarity_matrices


if __name__ == "__main__":
    try:
        matrices = main()
    except Exception as e:
        print(f"Error: {e}")
        raise