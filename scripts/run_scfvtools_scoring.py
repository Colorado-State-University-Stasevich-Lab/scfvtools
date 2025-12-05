#!/usr/bin/env python3

import argparse
import os
import pandas as pd

from scfvtools.anarci_utils import anarci_to_dataframe
from scfvtools.anarci_compare_utils import make_score_df


def main():
    parser = argparse.ArgumentParser(description="Run scfvtools ANARCI → scoring pipeline.")
    parser.add_argument(
        "--fasta", required=True,
        help="Input FASTA file containing sequences to score"
    )
    parser.add_argument(
        "--scheme", default="martin",
        help="ANARCI numbering scheme (default: martin)"
    )
    parser.add_argument(
        "--reference_csv", required=True,
        help="Reference DIFF CSV (e.g., consensus_csv/diff_H.csv)"
    )
    parser.add_argument(
        "--reference_name", default="diff_H",
        help="Name to label reference in output (default: diff_H)"
    )
    parser.add_argument(
        "--out_csv", required=True,
        help="Final scfvtools score CSV (one row per sequence)"
    )
    parser.add_argument(
        "--tmp_csv",
        help="Optional: where to write intermediate ANARCI CSV "
             "(default: derived from out_csv)"
    )

    args = parser.parse_args()

    # ----------------------------------------
    # Determine intermediate ANARCI CSV path
    # ----------------------------------------
    if args.tmp_csv:
        tmp_csv = args.tmp_csv
    else:
        tmp_csv = args.out_csv.replace(".csv", "_anarci.csv")

    # ----------------------------------------
    # STEP 1 — FASTA → ANARCI dataframe
    # ----------------------------------------
    print(f"[scfvtools] Running ANARCI on FASTA: {args.fasta}")
    df = anarci_to_dataframe(input_fasta=args.fasta, scheme=args.scheme)

    os.makedirs(os.path.dirname(tmp_csv), exist_ok=True)
    df.to_csv(tmp_csv, index=False)
    print(f"[scfvtools] Wrote ANARCI CSV → {tmp_csv}")

    # ----------------------------------------
    # STEP 2 — Score using reference DIFF CSV
    # ----------------------------------------
    # Run full scoring (per-position)
    raw_df = make_score_df(
        ref_csv=args.reference_csv,
        name1=args.reference_name,
        data_csv=tmp_csv
    )

    # Collapse to one score per sequence name
    summary_df = (
        raw_df[["name", "Score"]]
        .drop_duplicates()
    )

    # Write just the per-sequence summary
    summary_df.to_csv(args.out_csv, index=False)

    print(f"[scfvtools] Wrote per-sequence score CSV → {args.out_csv}")


if __name__ == "__main__":
    main()
