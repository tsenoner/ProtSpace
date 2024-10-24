import argparse
import json
import logging
import os
import sys
import warnings

import h5py
import numpy as np
import pandas as pd
from sklearn.decomposition import PCA
from sklearn.manifold import TSNE

warnings.filterwarnings("ignore", category=UserWarning, module="umap")
os.environ["KMP_WARNINGS"] = "off"

logger = logging.getLogger(__name__)


class DataProcessor:
    IDENTIFIER_COL = "identifier"
    PCA2_COLS = ["pca2_x", "pca2_y"]
    PCA3_COLS = ["pca3_x", "pca3_y", "pca3_z"]
    UMAP2_COLS = ["umap2_x", "umap2_y"]
    UMAP3_COLS = ["umap3_x", "umap3_y", "umap3_z"]
    TSNE2_COLS = ["tsne2_x", "tsne2_y"]
    TSNE3_COLS = ["tsne3_x", "tsne3_y", "tsne3_z"]
    PACMAP2_COLS = ["pacmap2_x", "pacmap2_y"]
    PACMAP3_COLS = ["pacmap3_x", "pacmap3_y", "pacmap3_z"]

    PROJECTION_COLS = {
        "pca2": PCA2_COLS,
        "pca3": PCA3_COLS,
        "umap2": UMAP2_COLS,
        "umap3": UMAP3_COLS,
        "tsne2": TSNE2_COLS,
        "tsne3": TSNE3_COLS,
        "pacmap2": PACMAP2_COLS,
        "pacmap3": PACMAP3_COLS,
    }

    def __init__(self, args):
        self.args = args
        self.projection_params = {}
        self.custom_names = args.custom_names or {}

    def process(self):
        logger.info("Starting data processing")
        headers, embs = load_hdf(h5_file=self.args.hdf)
        metadata = self._load_csv(self.args.csv)

        reduced_data = self._reduce_dimensions(embs)
        reduced_data[self.IDENTIFIER_COL] = headers

        df = self._merge_data(metadata, pd.DataFrame(reduced_data))
        json_data = self._df2json(df)

        self._update_json(json_data, self.args.output)
        logger.info("Data processing completed")

    def _load_csv(self, csv_file: str) -> pd.DataFrame:
        metadata = pd.read_csv(csv_file)
        if self.IDENTIFIER_COL not in metadata.columns:
            raise ValueError(
                f"CSV file must contain an '{self.IDENTIFIER_COL}' column"
            )
        logger.debug(f"Loaded {len(metadata)} entries from CSV file")
        return metadata

    def _merge_data(
        self, metadata: pd.DataFrame, reduced_data: pd.DataFrame
    ) -> pd.DataFrame:
        logger.debug("Merging metadata with reduced dimensions data")
        df = pd.merge(
            metadata, reduced_data, on=self.IDENTIFIER_COL, how="inner"
        )
        logger.debug(f"Merged {len(df)} entries")
        return df

    def _reduce_dimensions(self, embeddings):
        reduced_data = {}

        for method in self.args.methods:
            logger.info(f"Applying {method.upper()} dimension reduction")
            if method.startswith("pca"):
                pca_data = self._apply_pca(embeddings, int(method[-1]))
                reduced_data.update(pca_data)
            elif method.startswith("umap"):
                umap_data = self._apply_umap(embeddings, int(method[-1]))
                reduced_data.update(umap_data)
            elif method.startswith("tsne"):
                tsne_data = self._apply_tsne(embeddings, int(method[-1]))
                reduced_data.update(tsne_data)
            elif method.startswith("pacmap"):
                pacmap_data = self._apply_pacmap(embeddings, int(method[-1]))
                reduced_data.update(pacmap_data)

        return reduced_data

    def _apply_pca(self, embeddings, dimensions):
        pca = PCA(n_components=dimensions)
        pca_components = pca.fit_transform(embeddings)
        explained_variance_ratio = pca.explained_variance_ratio_

        self.projection_params[f"pca{dimensions}"] = {
            "n_components": dimensions,
            "explained_variance_ratio": explained_variance_ratio.tolist(),
        }

        logger.debug(f"PCA{dimensions} variance explained:")
        for i, var in enumerate(explained_variance_ratio, 1):
            logger.debug(f"  PC{i}: {var:.4f}")

        result = {}
        for i, col in enumerate(self.PROJECTION_COLS[f"pca{dimensions}"]):
            result[col] = pca_components[:, i]
        return result

    def _apply_umap(self, embeddings, dimensions):
        from umap import UMAP

        params = {
            k: v
            for k, v in vars(self.args).items()
            if k in ["n_neighbors", "min_dist", "metric"]
        }
        params["n_components"] = dimensions

        umap = UMAP(**params, random_state=42)
        umap_components = umap.fit_transform(embeddings)

        self.projection_params[f"umap{dimensions}"] = params
        logger.debug(f"UMAP{dimensions} parameters: {params}")

        result = {}
        for i, col in enumerate(self.PROJECTION_COLS[f"umap{dimensions}"]):
            result[col] = umap_components[:, i]
        return result

    def _apply_tsne(self, embeddings, dimensions):
        params = {
            k: v
            for k, v in vars(self.args).items()
            if k in ["perplexity", "learning_rate"]
        }
        params["n_components"] = dimensions

        tsne = TSNE(**params, random_state=42)
        tsne_components = tsne.fit_transform(embeddings)

        self.projection_params[f"tsne{dimensions}"] = params
        logger.debug(f"t-SNE{dimensions} parameters: {params}")

        result = {}
        for i, col in enumerate(self.PROJECTION_COLS[f"tsne{dimensions}"]):
            result[col] = tsne_components[:, i]
        return result

    def _apply_pacmap(self, embeddings, dimensions):
        from pacmap import PaCMAP
        params = {
            k: v
            for k, v in vars(self.args).items()
            if k in ["n_neighbors", "MN_ratio", "FP_ratio"]
        }
        params["n_components"] = dimensions
        params["n_neighbors"] = params.get("n_neighbors", 10)

        pacmap = PaCMAP(
            n_components=dimensions,
            n_neighbors=params["n_neighbors"],
            MN_ratio=params.get("MN_ratio", 0.5),
            FP_ratio=params.get("FP_ratio", 2.0),
            random_state=42
        )

        pacmap_components = pacmap.fit_transform(embeddings)

        self.projection_params[f"pacmap{dimensions}"] = params
        logger.debug(f"PaCMAP{dimensions} parameters: {params}")

        result = {}
        for i, col in enumerate(self.PROJECTION_COLS[f"pacmap{dimensions}"]):
            result[col] = pacmap_components[:, i]
        return result

    def _df2json(self, df):
        df = df.where(pd.notna(df), None)
        json_data = {"protein_data": {}, "projections": []}

        feature_columns = [
            col
            for col in df.columns
            if col
            not in [self.IDENTIFIER_COL]
            + sum(self.PROJECTION_COLS.values(), [])
        ]

        for _, row in df.iterrows():
            protein_id = row[self.IDENTIFIER_COL]
            json_data["protein_data"][protein_id] = {
                "features": {col: row[col] for col in feature_columns}
            }

        for method in self.args.methods:
            proj_cols = self.PROJECTION_COLS[method]
            if all(col in df.columns for col in proj_cols):
                custom_name = self.custom_names.get(method, method.upper())
                projection = {
                    "name": custom_name,
                    "dimensions": len(proj_cols),
                    "info": self._get_projection_info(method),
                    "data": [],
                }

                for _, row in df.iterrows():
                    coordinates = {
                        "x": row[proj_cols[0]],
                        "y": row[proj_cols[1]],
                    }
                    if len(proj_cols) == 3:
                        coordinates["z"] = row[proj_cols[2]]

                    projection["data"].append(
                        {
                            "identifier": row[self.IDENTIFIER_COL],
                            "coordinates": coordinates,
                        }
                    )

                json_data["projections"].append(projection)
        return json_data

    def _get_projection_info(self, method: str) -> dict:
        return self.projection_params.get(method, {})

    def _update_json(self, new_json_data, output_file):
        logger.info(f"Updating JSON data in: {output_file}")

        # Load existing JSON if it exists
        if os.path.exists(output_file):
            with open(output_file, 'r') as f:
                existing_data = json.load(f)
        else:
            existing_data = {"protein_data": {}, "projections": []}

        # Update protein_data
        existing_data["protein_data"].update(new_json_data["protein_data"])

        # Update projections
        existing_projections = {proj["name"]: proj for proj in existing_data["projections"]}
        for new_proj in new_json_data["projections"]:
            if new_proj["name"] in existing_projections:
                # Update existing projection
                existing_proj = existing_projections[new_proj["name"]]
                existing_proj["info"] = new_proj["info"]
                existing_proj["data"] = new_proj["data"]
            else:
                # Add new projection
                existing_data["projections"].append(new_proj)

        # Save updated JSON
        with open(output_file, 'w') as f:
            json.dump(existing_data, f, indent=2)


def setup_logging(log_level):
    # Remove all handlers associated with the root logger object
    for handler in logging.root.handlers[:]:
        logging.root.removeHandler(handler)

    # Set up our script's logger
    logger.setLevel(log_level)
    handler = logging.StreamHandler()
    formatter = logging.Formatter("%(levelname)s: %(message)s")
    handler.setFormatter(formatter)
    logger.addHandler(handler)


def load_hdf(h5_file: str) -> tuple[list[str], np.array]:
    embs, headers = [], []
    with h5py.File(h5_file, "r") as hdf_handle:
        for header, emb in hdf_handle.items():
            emb = np.array(emb).flatten()
            embs.append(emb)
            headers.append(header)
    embs = np.array(embs)
    logger.debug(f"Loaded {len(headers)} entries from HDF file")
    return headers, embs


def main():
    parser = argparse.ArgumentParser(
        description="Generate JSON data from HDF and CSV files"
    )
    parser.add_argument(
        "-H", "--hdf", required=True, help="Path to the HDF file"
    )
    parser.add_argument(
        "-c", "--csv", required=True, help="Path to the CSV feature file"
    )
    parser.add_argument(
        "-o", "--output", required=True, help="Path to the output JSON file"
    )
    parser.add_argument(
        "--methods",
        nargs="+",
        choices=["pca2", "pca3", "umap3", "umap2", "tsne3", "tsne2", "pacmap2", "pacmap3"],
        default=["pca3"],
        help="Dimension reduction technique(s) to use. Can specify multiple.",
    )
    parser.add_argument(
        "--custom-names",
        nargs="+",
        metavar="METHOD=NAME",
        help="Custom names for projections in format METHOD=NAME (e.g., pca3=MyPCA)",
    )
    parser.add_argument(
        "-v",
        "--verbose",
        action="count",
        default=0,
        help="Increase output verbosity (e.g., -v for INFO, -vv for DEBUG)",
    )

    # UMAP parameters
    parser.add_argument(
        "--n_neighbors", type=int, default=15, help="UMAP and PaCMAP n_neighbors parameter"
    )
    parser.add_argument(
        "--min_dist", type=float, default=0.1, help="UMAP min_dist parameter"
    )
    parser.add_argument(
        "--metric", default="euclidean", help="UMAP metric parameter"
    )

    # t-SNE parameters
    parser.add_argument(
        "--perplexity",
        type=int,
        default=30,
        help="t-SNE perplexity parameter",
    )
    parser.add_argument(
        "--learning_rate",
        type=int,
        default=200,
        help="t-SNE learning_rate parameter",
    )

    # PaCMAP parameters
    parser.add_argument(
        "--MN_ratio",
        type=float,
        default=0.5,
        help="PaCMAP MN_ratio parameter"
    )
    parser.add_argument(
        "--FP_ratio",
        type=float,
        default=2.0,
        help="PaCMAP FP_ratio parameter"
    )

    args = parser.parse_args()

    # Process custom names
    custom_names = {}
    if args.custom_names:
        for custom_name in args.custom_names:
            method, name = custom_name.split('=')
            custom_names[method] = name
    args.custom_names = custom_names

    # Set up logging based on verbosity level
    if args.verbose == 0:
        log_level = logging.WARNING
    elif args.verbose == 1:
        log_level = logging.INFO
    else:
        log_level = logging.DEBUG

    setup_logging(log_level)

    try:
        processor = DataProcessor(args)
        processor.process()
    except Exception as e:
        logger.error(f"Error: {str(e)}")
        sys.exit(1)


if __name__ == "__main__":
    main()