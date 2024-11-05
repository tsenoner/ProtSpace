#!/bin/bash

# Check if the input fasta file exists
if [ ! -f "mutated_sequences.fasta" ]; then
  echo "Error: File 'mutated_sequences.fasta' not found."
  exit 1
fi

# Get total number of sequences
N=$(grep -c '^>' mutated_sequences.fasta)

# Check if N is less than 1000
if [ "$N" -lt 1000 ]; then
  echo "Error: Total number of sequences ($N) is less than 1000."
  exit 1
fi

# Generate 999 random sequence numbers from 2 to N
seq 2 "$N" | shuf -n 999 > random_seq_nums.txt

# Include the first sequence and sort the sequence numbers
{ echo 1; cat random_seq_nums.txt; } | sort -n > selected_seq_nums.txt

# Extract the selected sequences from the fasta file
awk '
  BEGIN {
    # Read selected sequence numbers into an array
    while ((getline line < "selected_seq_nums.txt") > 0) {
      seqnum[line] = 1
    }
    close("selected_seq_nums.txt")
  }
  /^>/ {
    # Increment sequence counter at each header line
    seq++
    # Check if the sequence is selected
    inseq = (seq in seqnum)
  }
  {
    # If in a selected sequence, print the line
    if (inseq) print
  }
' mutated_sequences.fasta > subset_1000.fasta

# Clean up temporary files
rm random_seq_nums.txt selected_seq_nums.txt

echo "Random subset of 1000 sequences (including the first entry) saved to 'subset_1000.fasta'."
