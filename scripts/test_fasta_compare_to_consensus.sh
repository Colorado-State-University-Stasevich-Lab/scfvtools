#!/usr/bin/env bash
set -e

REF="../example_data/diff_H.csv"

# You can tweak these values to test behavior
GAP_PENALTY=-1.0
UNKNOWN_PENALTY=-1.0

echo "========================================"
echo "Testing FASTA input"
echo "========================================"

python fasta_compare_to_consensus.py \
  --ref_csv "$REF" \
  --name H \
  --data_fasta ../example_data/pathological.fasta \
  --gap_penalty "$GAP_PENALTY" \
  --unknown_penalty "$UNKNOWN_PENALTY"

echo
echo "========================================"
echo "Testing EXCEL input"
echo "========================================"

python fasta_compare_to_consensus.py \
  --ref_csv "$REF" \
  --name H \
  --excel ../example_data/test_scFvs.xlsx \
  --name_column name \
  --seq_column sequence \
  --gap_penalty "$GAP_PENALTY" \
  --unknown_penalty "$UNKNOWN_PENALTY"

echo
echo "All tests completed successfully."