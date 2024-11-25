# ProtSpace

ProtSpace is a powerful visualization tool for exploring protein embeddings and structures. It allows users to interactively visualize high-dimensional protein language model data in 2D or 3D space, color-code proteins based on various features, and view protein structures when available.

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
    - [Running ProtSpace](#running-protspace)
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

Try ProtSpace instantly using our Google Colab notebook:

[![Open In Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/tsenoner/ProtSpace/blob/main/examples/notebook/Run_ProtSpace.ipynb)

The notebook demonstrates:
- Installation and setup
- Data preparation
- Basic visualization

## Example Outputs

### 2D Scatter Plot (SVG)
![2D Scatter Plot Example](examples/out/3FTx/UMAP2_major_group.svg)

### 3D Interactive Plot
[View 3D Interactive Plot](https://tsenoner.github.io/ProtSpace/examples/out/3FTx/UMAP3_major_group.html)

## Installation

Using uv:
```bash
# Quick run
uvx protspace

# Permanent installation
uv tool install protspace
uv tool update-shell

# Latest GitHub version
uv tool install git+https://github.com/tsenoner/ProtSpace.git
uv tool update-shell
```

## Usage

### Data Preparation
```bash
uvx --from protspace protspace-json -i embeddings.h5 -m features.csv -o output.json --methods pca3 umap2 tsne2
```

### Running ProtSpace
```bash
protspace output.json [--pdb_zip pdb_files.zip] [--port 8050]
```

Access the interface at `http://localhost:8050`

## Features

- Interactive 2D/3D visualization (PCA, UMAP, t-SNE)
- Feature-based coloring and marker styling
- Protein structure visualization (with PDB files)
- Search and highlight functionality
- High-quality plot exports
- Responsive web interface

## Data Preparation

The `protspace-json` command supports:

### Required Arguments
- `-i, --input`: HDF file (.h5) or similarity matrix (.csv)
- `-m, --metadata`: CSV file with features
- `-o, --output`: Output JSON path
- `--methods`: Reduction methods (e.g., pca2, tsne3, umap2)

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
   - CSV with 'identifier' column
   - Additional columns for features

3. **Structures**
   - ZIP containing PDB/CIF files
   - Filenames match identifiers (dots replaced with underscores)

### Output
- JSON containing:
  - Protein features
  - Projection coordinates
  - Visualization state (colors, shapes)
  - Structure references