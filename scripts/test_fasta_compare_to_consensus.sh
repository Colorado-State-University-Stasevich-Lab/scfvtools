#!/usr/bin/env bash
set -e

REF="../example_data/diff_H.csv"

echo "=== FASTA ==="
python fasta_compare_to_consensus.py \
    --ref_csv "$REF" \
    --name H \
    --data_fasta ../example_data/WNV_5D4.fasta \
    --out ./WNV_5D4_consensus_scores.csv

echo "=== EXCEL ==="
python fasta_compare_to_consensus.py \
    --ref_csv "$REF" \
    --name H \
    --excel ../example_data/test_scFvs.xlsx \
    --name_column name \
    --seq_column sequence \
    --out ./test_scFvs_consensus_scores.csv
