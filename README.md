# ProtSpace

ProtSpace is a visualization tool for exploring protein embeddings or similarity matrix along their 3D protein structures. It allows users to interactively visualize high-dimensional protein language model data in 2D or 3D space, color-code proteins based on various features, and view protein structures when available.

## Table of Contents

- [ProtSpace](#protspace)
  - [Table of Contents](#table-of-contents)
  - [Quick Start with Google Colab](#quick-start-with-google-colab)
  - [Example Outputs](#example-outputs)
    - [2D Scatter Plot (SVG)](#2d-scatter-plot-svg)
    - [3D Interactive Plot](#3d-interactive-plot)
  - [Installation](#installation)
  - [Usage](#usage)
    - [Data Preparation](#data-preparation)
    - [Running protspace](#running-protspace)
  - [Features](#features)
  - [Data Preparation](#data-preparation-1)
    - [Required Arguments](#required-arguments)
    - [Optional Arguments](#optional-arguments)
    - [Method-Specific Parameters](#method-specific-parameters)
  - [Custom Feature Styling](#custom-feature-styling)
  - [File Formats](#file-formats)
    - [Input](#input)
    - [Output](#output)

## Quick Start with Google Colab

Try ProtSpace instantly using our Google Colab notebooks:

**Note**: Some Google Colab functionalities may not work properly in Safari browsers. For the best experience, we recommend using Chrome or Firefox.

1. **Explore Pre-computed Visualizations**:
[![Open Explorer In Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/tsenoner/protspace/blob/main/examples/notebook/Explore_ProtSpace.ipynb)

2. **Generate Protein Embeddings**:
[![Open Embeddings In Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/tsenoner/protspace/blob/main/examples/notebook/ClickThrough_GenerateEmbeddings.ipynb)

3. **Full Pipeline Demo**:
[![Open Pipeline In Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/tsenoner/protspace/blob/main/examples/notebook/Run_ProtSpace.ipynb)

## Example Outputs

### 2D Scatter Plot (SVG)

![2D Scatter Plot Example](https://tsenoner.github.io/protspace/examples/out/toxins/protein_category_umap.svg)

### 3D Interactive Plot

[View 3D Interactive Plot](https://tsenoner.github.io/protspace/examples/out/3FTx/UMAP3_major_group.html)

## Installation

```bash
pip install protspace
```

## Usage

### Data Preparation

```bash
protspace-json -i embeddings.h5 -m features.csv -o output.json --methods pca3 umap2 tsne2
```

### Running protspace

```bash
protspace output.json [--pdb_zip pdb_files.zip] [--port 8050]
```

Access the interface at `http://localhost:8050`

## Features

- Interactive 2D/3D visualization with multiple dimensionality reduction methods:
  - Principal Component Analysis (PCA)
  - Multidimensional Scaling (MDS)
  - Uniform Manifold Approximation and Projection (UMAP)
  - t-Distributed Stochastic Neighbor Embedding (t-SNE)
  - Pairwise Controlled Manifold Approximation (PaCMAP)
- Feature-based coloring and marker styling
- Protein structure visualization (with PDB files)
- Search and highlight functionality
- High-quality plot exports
- Responsive web interface

## Data Preparation

The `protspace-json` command supports:

### Required Arguments

- `-i, --input`: HDF file (.h5) or similarity matrix (.csv)
- `-m, --metadata`: CSV file with features (first column must be named "identifier" and match IDs in HDF5/similarity matrix)
- `-o, --output`: Output JSON path
- `--methods`: Reduction methods (e.g., pca2, tsne3, umap2, pacmap2, mds2)

### Optional Arguments

- `--custom_names`: Custom projection names (e.g., pca2=PCA_2D)
- `--verbose`: Increase output verbosity

### Method-Specific Parameters

- UMAP:
  - `--n_neighbors`: Number of neighbors (default: 15)
  - `--min_dist`: Minimum distance (default: 0.1)
- t-SNE:
  - `--perplexity`: Perplexity value (default: 30)
  - `--learning_rate`: Learning rate (default: 200)
- PaCMAP:
  - `--mn_ratio`: MN ratio (default: 0.5)
  - `--fp_ratio`: FP ratio (default: 2.0)
- MDS:
  - `--n_init`: Number of initializations (default: 4)
  - `--max_iter`: Maximum iterations (default: 300)

## Custom Feature Styling

Use `protspace-feature-colors` to customize feature appearance:

```bash
protspace-feature-colors input.json output.json --feature_styles '{
  "feature_name": {
    "colors": {
      "value1": "#FF0000",
      "value2": "#00FF00"
    },
    "shapes": {
      "value1": "circle",
      "value2": "square"
    }
  }
}'
```

Available shapes: circle, circle-open, cross, diamond, diamond-open, square, square-open, x

## File Formats

### Input

1. **Embeddings/Similarity**
   - HDF5 (.h5) for embeddings
   - CSV for similarity matrix

2. **Metadata**
   - CSV with mandatory 'identifier' column matching IDs in embeddings/similarity data
   - Additional columns for features

3. **Structures**
   - ZIP containing PDB/CIF files
   - Filenames match identifiers (dots replaced with underscores)

### Output

- JSON containing:
  - Protein features
  - Projection coordinates
  - Visualization state (colors, shapes)