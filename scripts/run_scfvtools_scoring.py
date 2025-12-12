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
        help="Reference DIFF CSV (e.g., example_data/diff_H.csv)"
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
    raw_df.to_csv(args.out_csv, index=False)
    print(f"✔ Wrote scfvtools score CSV → {args.out_csv}")



    # # ============================================================
    # # STEP 3 — Append consensus/design comparison in AF2-style
    # # ============================================================
    # try:
    #     import scfvtools as scfv
    #     from pathlib import Path

    #     summary_html = Path(args.out_csv).with_suffix("").as_posix() + "_summary.html"

    #     print(f"[scfvtools] Appending consensus/design comparison → {summary_html}")

    #     # Open a scrolling window like the others
    #     with open(summary_html, "a") as f:
    #         f.write('\n<div class="seq_window" '
    #                 'style="border:1px solid #bbb; padding:10px; margin:25px 0; '
    #                 'max-height:450px; overflow-y:auto; background:#fafafa;">\n')
    #         f.write('<h2 style="margin-top:0;">Consensus vs All Designs</h2>\n')

    #     # Consensus directory based on reference_csv
    #     ref_dir = Path(args.reference_csv).parent

    #     # Embedded ANARCI HTML inside the window
    #     scfv.show_anarci_html(
    #         str(ref_dir / "consensus_H_1_0.csv"),
    #         outfile=summary_html,
    #         number=True, chain="H",
    #         legend=True, region="ALL",
    #         show_header=True
    #     )
    #     scfv.show_anarci_html(
    #         str(ref_dir / "consensus_H_0_0.csv"),
    #         outfile=summary_html,
    #         number=False, chain="H",
    #         legend=False, region="ALL",
    #         show_header=False
    #     )
    #     scfv.show_anarci_html(
    #         args.reference_csv,
    #         outfile=summary_html,
    #         number=False, chain="H",
    #         legend=False, region="ALL",
    #         show_header=False
    #     )

    #     # Designs block
    #     with open(summary_html, "a") as f:
    #         f.write('<h3>All Designs Compared to Consensus</h3>\n')

    #     scfv.show_anarci_html(
    #         tmp_csv,     # ANARCI CSV of all designs
    #         outfile=summary_html,
    #         number=False, chain="H",
    #         legend=False, region="ALL",
    #         show_header=True
    #     )

    #     # Close the window
    #     with open(summary_html, "a") as f:
    #         f.write("</div>\n\n")

    # except Exception as e:
    #     print("[WARNING] Could not append consensus/design HTML block:")
    #     print(e)





if __name__ == "__main__":
    main()
