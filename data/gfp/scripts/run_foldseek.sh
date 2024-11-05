#!/bin/bash

# Function to display usage
usage() {
    echo "Usage: $0 -i <input_dir> [-e <e_value>] [-s <sensitivity>] [-c <coverage>] [-m <max_seqs>]"
    echo "Options:"
    echo "  -i  Input directory containing structure files (required)"
    echo "  -e  E-value cutoff (default: 0.001)"
    echo "  -s  Sensitivity value (default: 7.5)"
    echo "  -c  Coverage value (default: 0.8)"
    echo "  -m  Maximum number of sequence matches per query (default: 300)"
    echo "  -h  Display this help message"
    exit 1
}

# Default values
EVALUE=0.001
SENSITIVITY=7.5
COVERAGE=0.8
MAX_SEQS=300

# Parse command line arguments
while getopts "i:e:s:c:m:h" opt; do
    case $opt in
        i) INPUT_DIR="$OPTARG";;
        e) EVALUE="$OPTARG";;
        s) SENSITIVITY="$OPTARG";;
        c) COVERAGE="$OPTARG";;
        m) MAX_SEQS="$OPTARG";;
        h) usage;;
        ?) usage;;
    esac
done

# Check if input directory is provided
if [ -z "$INPUT_DIR" ]; then
    echo "Error: Input directory is required"
    usage
fi

# Check if input directory exists
if [ ! -d "$INPUT_DIR" ]; then
    echo "Error: Input directory '$INPUT_DIR' not found"
    exit 1
fi

# Create directory structure
BASENAME=$(basename "$INPUT_DIR")
FOLDSEEK_DIR="foldseek_${BASENAME}"
TMP_DIR="${FOLDSEEK_DIR}/tmp"

mkdir -p "$TMP_DIR"

# Function to handle errors
check_error() {
    if [ $? -ne 0 ]; then
        echo "Error: $1"
        exit 1
    fi
}

echo "Starting Foldseek all-vs-all search..."
echo "E-value cutoff: $EVALUE"
echo "Sensitivity: $SENSITIVITY"
echo "Coverage: $COVERAGE"
echo "Maximum sequences per query: $MAX_SEQS"

# Create databases
echo "Creating databases..."
foldseek createdb "$INPUT_DIR" "${TMP_DIR}/query_db" \
    || check_error "Failed to create query database"
foldseek createdb "$INPUT_DIR" "${TMP_DIR}/target_db" \
    || check_error "Failed to create target database"

# Perform search
echo "Performing all-vs-all search..."
foldseek search \
    "${TMP_DIR}/query_db" \
    "${TMP_DIR}/target_db" \
    "${TMP_DIR}/aln" \
    "$TMP_DIR" \
    -e "$EVALUE" \
    -s "$SENSITIVITY" \
    --cov-mode 0 \
    -c "$COVERAGE" \
    --max-seqs "$MAX_SEQS" \
    # --exhaustive-search 1 \
    -a 1 \
    || check_error "Search failed"

# Convert results to readable format
echo "Converting results to TSV format..."
foldseek convertalis \
    "${TMP_DIR}/query_db" \
    "${TMP_DIR}/target_db" \
    "${TMP_DIR}/aln" \
    "${FOLDSEEK_DIR}/results.tsv" \
    # --exact-tmscore 1 \
    --format-mode 4 \
    --format-output \
    query,target,fident,evalue,bits,lddt,alntmscore,rmsd \
    || check_error "Failed to convert results"

echo "All done! Results can be found in: ${FOLDSEEK_DIR}/results.tsv"

# Optional: Cleanup tmp directory
#rm -rf "$TMP_DIR"