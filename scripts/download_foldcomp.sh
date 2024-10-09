#!/bin/bash
set -euo pipefail

usage() {
    echo "Usage: $0 <base_file> <output_dir>"
    echo "Downloads Foldcomp files from https://foldcomp.steineggerlab.workers.dev"
    echo
    echo "Arguments:"
    echo "  base_file   Base name of the file to download"
    echo "  output_dir  Directory to save the downloaded files"
    exit 1
}

[ $# -eq 2 ] || usage

BASE_URL="https://foldcomp.steineggerlab.workers.dev"
BASE_FILE="$1"
OUTPUT_DIR="$2"
EXTENSIONS=("lookup" "index" "dbtype" "")

mkdir -p "$OUTPUT_DIR"

download_file() {
    local ext="$1"
    local file_name="${BASE_FILE}${ext:+.$ext}"
    echo "Downloading $file_name..."
    curl -o "$OUTPUT_DIR/$file_name" "$BASE_URL/$file_name"
    echo "Finished downloading $file_name"
}

for ext in "${EXTENSIONS[@]}"; do
    download_file "$ext"
done