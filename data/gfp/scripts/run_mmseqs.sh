#!/bin/bash

# Function to display usage
usage() {
    echo "Usage: $0 -f <fasta_file> [-s <sensitivity>] [-c <coverage>] [-m <max_seqs>]"
    echo "Options:"
    echo "  -f  Input FASTA file (required)"
    echo "  -s  Sensitivity value (default: 7.5)"
    echo "  -c  Coverage value (default: 0.8)"
    echo "  -m  Maximum number of sequence matches per query (default: 300)"
    echo "  -h  Display this help message"
    exit 1
}

# Default values
SENSITIVITY=7.5
COVERAGE=0.8
MAX_SEQS=300

# Parse command line arguments
while getopts "f:s:c:m:h" opt; do
    case $opt in
        f) FASTA_FILE="$OPTARG";;
        s) SENSITIVITY="$OPTARG";;
        c) COVERAGE="$OPTARG";;
        m) MAX_SEQS="$OPTARG";;
        h) usage;;
        ?) usage;;
    esac
done

# Check if FASTA file is provided
if [ -z "$FASTA_FILE" ]; then
    echo "Error: FASTA file is required"
    usage
fi

# Check if FASTA file exists
if [ ! -f "$FASTA_FILE" ]; then
    echo "Error: FASTA file '$FASTA_FILE' not found"
    exit 1
fi

# Create directory structure
BASENAME=$(basename "$FASTA_FILE" .fasta)
MMSEQS_DIR="mmseqs_${BASENAME}"
TMP_DIR="${MMSEQS_DIR}/tmp"

mkdir -p "$TMP_DIR"

# Function to handle errors
check_error() {
    if [ $? -ne 0 ]; then
        echo "Error: $1"
        exit 1
    fi
}

echo "Starting MMseqs2 all-vs-all search..."
echo "Using sensitivity: $SENSITIVITY"
echo "Using coverage: $COVERAGE"
echo "Maximum sequences per query: $MAX_SEQS"

# Create database
echo "Creating database..."
mmseqs createdb "$FASTA_FILE" "${TMP_DIR}/sequences_db" \
    || check_error "Failed to create database"

# Perform search
echo "Performing all-vs-all search..."
mmseqs search \
    "${TMP_DIR}/sequences_db" \
    "${TMP_DIR}/sequences_db" \
    "${TMP_DIR}/search_results" \
    "${TMP_DIR}" \
    -s "$SENSITIVITY" \
    --cov-mode 2 \
    -c "$COVERAGE" \
    --max-seqs "$MAX_SEQS" \
    --exhaustive-search-filter 1 \
    --add-self-matches 1 \
    --prefilter-mode 2 \
    -e "inf" \
    || check_error "Search failed"

# Convert results to readable format
echo "Converting results to CSV format..."
mmseqs convertalis \
    "${TMP_DIR}/sequences_db" \
    "${TMP_DIR}/sequences_db" \
    "${TMP_DIR}/search_results" \
    "${MMSEQS_DIR}/results.tsv" \
    --format-mode 4 \
    --format-output \
    query,target,fident,evalue,bits \
    || check_error "Failed to convert results"

echo "All done! Results can be found in: ${MMSEQS_DIR}/results.tsv"

# Optional: Cleanup tmp directory
#rm -rf "$TMP_DIR"