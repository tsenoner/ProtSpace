import argparse
import json
import logging
from abc import ABC, abstractmethod
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple, Union

import h5py
import numpy as np
import pandas as pd
from sklearn.decomposition import PCA
from sklearn.manifold import MDS, TSNE

# Configure logging
logging.basicConfig(format="%(levelname)s: %(message)s")
logger = logging.getLogger(__name__)

# Valid file extensions
EMBEDDING_EXTENSIONS = {'.hdf', '.hdf5', '.h5'}

@dataclass
class DimensionReductionConfig:
    """Configuration for dimension reduction methods."""
    n_components: int
    # General parameters
    n_neighbors: int = 15
    metric: str = "euclidean"
    random_state: int = 42
    # UMAP specific
    min_dist: float = 0.1
    # t-SNE specific
    perplexity: int = 30
    learning_rate: int = 200
    # PaCMAP specific
    mn_ratio: float = 0.5
    fp_ratio: float = 2.0
    # MDS specific
    n_init: int = 4
    max_iter: int = 300
    eps: float = 1e-3
    dissimilarity: str = "euclidean"

class DimensionReducer(ABC):
    """Abstract base class for dimension reduction methods."""

    def __init__(self, config: DimensionReductionConfig):
        self.config = config

    @abstractmethod
    def fit_transform(self, data: np.ndarray) -> np.ndarray:
        """Transform data to lower dimensions."""
        pass

    @abstractmethod
    def get_params(self) -> Dict[str, Any]:
        """Get parameters used for the reduction."""
        pass

class PCAReducer(DimensionReducer):
    """Principal Component Analysis reduction."""
    def fit_transform(self, data: np.ndarray) -> np.ndarray:
        pca = PCA(
            n_components=self.config.n_components,
            random_state=self.config.random_state
        )
        result = pca.fit_transform(data)
        self.explained_variance = pca.explained_variance_ratio_.tolist()
        return result

    def get_params(self) -> Dict[str, Any]:
        return {
            "n_components": self.config.n_components,
            "explained_variance_ratio": self.explained_variance
        }

class TSNEReducer(DimensionReducer):
    """t-SNE (t-Distributed Stochastic Neighbor Embedding) reduction."""
    def fit_transform(self, data: np.ndarray) -> np.ndarray:
        return TSNE(
            n_components=self.config.n_components,
            perplexity=self.config.perplexity,
            learning_rate=self.config.learning_rate,
            random_state=self.config.random_state,
            metric=self.config.metric
        ).fit_transform(data)

    def get_params(self) -> Dict[str, Any]:
        return {
            "n_components": self.config.n_components,
            "perplexity": self.config.perplexity,
            "learning_rate": self.config.learning_rate,
            "metric": self.config.metric
        }

class UMAPReducer(DimensionReducer):
    """UMAP (Uniform Manifold Approximation and Projection) reduction."""
    def fit_transform(self, data: np.ndarray) -> np.ndarray:
        from umap import UMAP
        return UMAP(
            n_components=self.config.n_components,
            n_neighbors=self.config.n_neighbors,
            min_dist=self.config.min_dist,
            metric=self.config.metric,
            random_state=self.config.random_state
        ).fit_transform(data)

    def get_params(self) -> Dict[str, Any]:
        return {
            "n_components": self.config.n_components,
            "n_neighbors": self.config.n_neighbors,
            "min_dist": self.config.min_dist,
            "metric": self.config.metric
        }

class PaCMAPReducer(DimensionReducer):
    """PaCMAP (Pairwise Controlled Manifold Approximation) reduction."""
    def fit_transform(self, data: np.ndarray) -> np.ndarray:
        from pacmap import PaCMAP
        return PaCMAP(
            n_components=self.config.n_components,
            n_neighbors=self.config.n_neighbors,
            MN_ratio=self.config.mn_ratio,
            FP_ratio=self.config.fp_ratio,
            random_state=self.config.random_state
        ).fit_transform(data)

    def get_params(self) -> Dict[str, Any]:
        return {
            "n_components": self.config.n_components,
            "n_neighbors": self.config.n_neighbors,
            "MN_ratio": self.config.mn_ratio,
            "FP_ratio": self.config.fp_ratio
        }

class MDSReducer(DimensionReducer):
    """Multidimensional Scaling reduction."""
    def fit_transform(self, data: np.ndarray) -> np.ndarray:
        return MDS(
            n_components=self.config.n_components,
            metric=bool(self.config.dissimilarity == "euclidean"),
            n_init=self.config.n_init,
            max_iter=self.config.max_iter,
            eps=self.config.eps,
            dissimilarity=self.config.dissimilarity,
            random_state=self.config.random_state
        ).fit_transform(data)

    def get_params(self) -> Dict[str, Any]:
        return {
            "n_components": self.config.n_components,
            "dissimilarity": self.config.dissimilarity,
            "n_init": self.config.n_init,
            "max_iter": self.config.max_iter,
            "eps": self.config.eps
        }

class DataProcessor:
    """Main class for processing and reducing dimensionality of data."""

    REDUCERS = {
        "pca": PCAReducer,
        "tsne": TSNEReducer,
        "umap": UMAPReducer,
        "pacmap": PaCMAPReducer,
        "mds": MDSReducer
    }

    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.identifier_col = "identifier"

    @staticmethod
    def load_data(input_path: Path, metadata_path: Path) -> Tuple[pd.DataFrame, np.ndarray, List[str]]:
        """Load and align input data with metadata, handling missing values gracefully."""
        # Load metadata if available
        try:
            metadata = pd.read_csv(metadata_path)
            if "identifier" not in metadata.columns:
                logger.warning("Metadata CSV missing 'identifier' column - creating empty metadata")
                metadata = pd.DataFrame(columns=["identifier"])
        except Exception as e:
            logger.warning(f"Could not load metadata ({str(e)}) - creating empty metadata")
            metadata = pd.DataFrame(columns=["identifier"])

        # Load input data based on file extension
        if input_path.suffix.lower() in EMBEDDING_EXTENSIONS:
            logger.info("Loading embeddings from HDF file")
            data, headers = [], []
            with h5py.File(input_path, "r") as hdf_handle:
                for header, emb in hdf_handle.items():
                    emb = np.array(emb).flatten()
                    data.append(emb)
                    headers.append(header)
            data = np.array(data)

        elif input_path.suffix.lower() == '.csv':
            logger.info("Loading similarity matrix from CSV file")
            sim_matrix = pd.read_csv(input_path, index_col=0)
            if not sim_matrix.index.equals(sim_matrix.columns):
                raise ValueError("Similarity matrix must have matching row and column labels")

            headers = sim_matrix.index.tolist()
            data = sim_matrix.values

            if not np.allclose(data, data.T, rtol=1e-5, atol=1e-8):
                logger.warning("Similarity matrix is not perfectly symmetric - using (A + A.T)/2")
                data = (data + data.T) / 2

        else:
            raise ValueError("Input file must be either HDF (.hdf, .hdf5, .h5) or CSV (.csv)")

        # Create full metadata with NaN for missing entries
        full_metadata = pd.DataFrame({'identifier': headers})
        if len(metadata.columns) > 1:
            full_metadata = full_metadata.merge(
                metadata.drop_duplicates('identifier'),
                on='identifier',
                how='left'
            )

        return full_metadata, data, headers

    def process_reduction(self, data: np.ndarray, method: str, dims: int) -> Dict[str, Any]:
        """Process a single reduction method."""
        config = DimensionReductionConfig(n_components=dims, **self.config)
        reducer = self.REDUCERS[method](config)
        reduced_data = reducer.fit_transform(data)

        return {
            "name": f"{method.upper()}{dims}",
            "dimensions": dims,
            "info": reducer.get_params(),
            "data": reduced_data
        }

    def create_output(self, metadata: pd.DataFrame, reductions: List[Dict[str, Any]],
                     headers: List[str]) -> Dict[str, Any]:
        """Create the final output dictionary."""
        output = {
            "protein_data": {},
            "projections": []
        }

        # Process features
        for _, row in metadata.iterrows():
            protein_id = row[self.identifier_col]
            features = row.drop(self.identifier_col).to_dict()
            output["protein_data"][protein_id] = {"features": features}

        # Process projections
        for reduction in reductions:
            projection = {
                "name": reduction["name"],
                "dimensions": reduction["dimensions"],
                "info": reduction["info"],
                "data": []
            }

            for i, header in enumerate(headers):
                coordinates = {
                    "x": float(reduction["data"][i][0]),
                    "y": float(reduction["data"][i][1])
                }
                if reduction["dimensions"] == 3:
                    coordinates["z"] = float(reduction["data"][i][2])

                projection["data"].append({
                    "identifier": header,
                    "coordinates": coordinates
                })

            output["projections"].append(projection)

        return output

def save_output(data: Dict[str, Any], output_path: Path):
    """Save output data to JSON file."""
    if output_path.exists():
        with output_path.open('r') as f:
            existing = json.load(f)
            existing["protein_data"].update(data["protein_data"])

            # Update or add projections
            existing_projs = {p["name"]: p for p in existing["projections"]}
            for new_proj in data["projections"]:
                existing_projs[new_proj["name"]] = new_proj
            existing["projections"] = list(existing_projs.values())

        data = existing

    with output_path.open('w') as f:
        json.dump(data, f, indent=2)

def main():
    parser = argparse.ArgumentParser(
        description="Dimensionality reduction for protein embeddings or similarity matrices",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter
    )

    # Required arguments
    parser.add_argument(
        "-i", "--input", type=Path, required=True,
        help="Path to input data: HDF file (.hdf, .hdf5, .h5) for embeddings or CSV file for similarity matrix"
    )
    parser.add_argument(
        "-m", "--metadata", type=Path, required=True,
        help="Path to CSV file containing metadata and features"
    )
    parser.add_argument(
        "-o", "--output", type=Path, required=True,
        help="Path to output JSON file"
    )

    # Reduction methods
    parser.add_argument(
        "--methods", nargs="+", default=["pca3"],
        help="Reduction methods to use (e.g., pca2, tsne3, mds2). Format: method_name + dimensions"
    )

    # Verbosity control
    parser.add_argument(
        "-v", "--verbose", action="count", default=0,
        help="Increase output verbosity (-v for INFO, -vv for DEBUG)"
    )

    # General parameters
    general_group = parser.add_argument_group('General Parameters')
    general_group.add_argument(
        "--metric", default="euclidean",
        help="Distance metric to use (applies to UMAP, t-SNE, MDS)"
    )
    general_group.add_argument(
        "--random-state", type=int, default=42,
        help="Random seed for reproducibility"
    )

    # UMAP parameters
    umap_group = parser.add_argument_group('UMAP Parameters')
    umap_group.add_argument(
        "--n_neighbors", type=int, default=15,
        help="Number of neighbors to consider (UMAP, PaCMAP)"
    )
    umap_group.add_argument(
        "--min_dist", type=float, default=0.1,
        help="Minimum distance between points in UMAP"
    )

    # t-SNE parameters
    tsne_group = parser.add_argument_group('t-SNE Parameters')
    tsne_group.add_argument(
        "--perplexity", type=int, default=30,
        help="Perplexity parameter for t-SNE"
    )
    tsne_group.add_argument(
        "--learning_rate", type=int, default=200,
        help="Learning rate for t-SNE"
    )

    # PaCMAP parameters
    pacmap_group = parser.add_argument_group('PaCMAP Parameters')
    pacmap_group.add_argument(
        "--mn_ratio", type=float, default=0.5,
        help="MN ratio for PaCMAP"
    )
    pacmap_group.add_argument(
        "--fp_ratio", type=float, default=2.0,
        help="FP ratio for PaCMAP"
    )

    # MDS parameters
    mds_group = parser.add_argument_group('MDS Parameters')
    mds_group.add_argument(
        "--n_init", type=int, default=4,
        help="Number of initialization runs for MDS"
    )
    mds_group.add_argument(
        "--max_iter", type=int, default=300,
        help="Maximum number of iterations for MDS"
    )
    mds_group.add_argument(
        "--eps", type=float, default=1e-3,
        help="Relative tolerance for MDS convergence"
    )
    mds_group.add_argument(
        "--dissimilarity", choices=['euclidean', 'precomputed'],
        default='euclidean',
        help="Dissimilarity measure for MDS"
    )

    args = parser.parse_args()

    # Set logging level
    logger.setLevel([logging.WARNING, logging.INFO, logging.DEBUG][min(args.verbose, 2)])

    try:
        # Process data
        processor = DataProcessor(vars(args))
        metadata, data, headers = processor.load_data(args.input, args.metadata)

        # Process each method
        reductions = []
        for method_spec in args.methods:
            method = ''.join(filter(str.isalpha, method_spec))
            dims = int(''.join(filter(str.isdigit, method_spec)))

            if method not in processor.REDUCERS:
                raise ValueError(f"Unknown reduction method: {method}")

            logger.info(f"Applying {method.upper()}{dims} reduction")
            reductions.append(processor.process_reduction(data, method, dims))

        # Create and save output
        output = processor.create_output(metadata, reductions, headers)
        save_output(output, args.output)
        logger.info(f"Successfully processed {len(headers)} items using {len(args.methods)} reduction methods")

    except Exception as e:
        logger.error(f"Error: {str(e)}")
        raise

if __name__ == "__main__":
    main()