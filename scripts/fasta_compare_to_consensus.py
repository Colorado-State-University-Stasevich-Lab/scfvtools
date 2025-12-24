from pathlib import Path
import argparse
import scfvtools as scfv


# ------------------------------------------------------------
# Helper functions for automatic naming
# ------------------------------------------------------------
def auto_names_from_fasta(path):
    """Given input FASTA X.fasta → X_consensus_scores.csv"""
    p = Path(path)
    stem = p.stem
    return f"{stem}_consensus_scores.csv"


def auto_names_from_excel(path):
    """
    Given Excel X.xlsx →
       raw FASTA = X_raw_sequences.fasta
       scores    = X_consensus_scores.csv
    """
    p = Path(path)
    stem = p.stem
    raw_fasta = f"{stem}_raw_sequences.fasta"
    out_score = f"{stem}_consensus_scores.csv"
    return raw_fasta, out_score


def main():
    parser = argparse.ArgumentParser(
        description=(
            "scFv FASTA + consensus CSV → scoring of scFv sequences\n"
            "Optionally: Excel → FASTA → scoring"
        )
    )

    # ------------------------------------------------------------
    # Required
    # ------------------------------------------------------------
    parser.add_argument("--ref_csv", required=True,
                        help="Path to reference consensus CSV (e.g. diff_H.csv)")
    parser.add_argument("--name", required=True,
                        help="Name of consensus sequence in reference")

    # FASTA mode
    parser.add_argument("--data_fasta", required=False,
                        help="FASTA containing sequences to score")

    # Excel mode
    parser.add_argument("--excel", required=False,
                        help="Excel file to convert into FASTA before scoring")
    parser.add_argument("--name_column", required=False,
                        help="Column in Excel containing sequence names")
    parser.add_argument("--seq_column", required=False,
                        help="Column in Excel containing amino-acid sequences")
    parser.add_argument("--contains", required=False, default=None,
                        help="Optional substring filter to include only rows containing this string")

    # Output options (optional now)
    parser.add_argument("--out", required=False,
                        help="Output CSV path for scored sequences")
    parser.add_argument("--raw", required=False,
                        help="Raw FASTA output when converting Excel → FASTA")

    args = parser.parse_args()

    # ============================================================
    # CASE 1 — Excel input provided
    # ============================================================
    if args.excel is not None:
        print("STEP 1: Reading Excel and writing FASTA...")

        # Auto-generate names if not provided
        raw_default, out_default = auto_names_from_excel(args.excel)

        if args.raw is None:
            args.raw = raw_default
            print(f"[AUTO] Using raw FASTA: {args.raw}")

        if args.out is None:
            args.out = out_default
            print(f"[AUTO] Using OUT file: {args.out}")

        records = scfv.read_excel_to_fasta(
            excel_path=args.excel,
            name_column=args.name_column,
            sequence_column=args.seq_column,
            output_fasta=args.raw,
            contains_string=args.contains,
            annotation_columns=None
        )

        print(f"✔ Wrote {len(records)} sequences → {args.raw}")

        fasta_path = args.raw

    # ============================================================
    # CASE 2 — FASTA input
    # ============================================================
    else:
        if args.data_fasta is None:
            raise ValueError("Must provide either --data_fasta or --excel.")

        fasta_path = args.data_fasta

        # Auto-name OUT if missing
        if args.out is None:
            args.out = auto_names_from_fasta(args.data_fasta)
            print(f"[AUTO] Using OUT file: {args.out}")

    # ============================================================
    # Continue with your original workflow
    # ============================================================
    print(f"[INFO] Running make_score_df with:")
    print(f"       ref_csv     = {args.ref_csv}")
    print(f"       consensus   = {args.name}")
    print(f"       data_fasta  = {fasta_path}")
    print(f"       outfile     = {args.out}")

    # ------------------------------------------------------------
    # STEP: FASTA → ANARCI CSV
    # ------------------------------------------------------------
    df = scfv.anarci_to_dataframe(
        input_fasta=fasta_path,
        scheme="martin"
    )

    inpath = Path(fasta_path)
    outfile_csv = Path("../output_dir") / inpath.with_suffix(".csv").name
    df.to_csv(outfile_csv, index=False)

    # ------------------------------------------------------------
    # STEP: Score against consensus
    # ------------------------------------------------------------
    score_df = scfv.make_score_df(
        ref_csv=args.ref_csv,
        name1=args.name,
        data_csv=outfile_csv,
        outfile=args.out
    )

    print(f"[INFO] Score dataframe written to: {args.out}")

    # ------------------------------------------------------------
    # STEP: HTML output
    # ------------------------------------------------------------
    outfile_html = Path("../output_dir") / inpath.with_suffix(".html").name
    print("[INFO] Displaying alignment (H chain)...")

    scfv.html_start(outfile_html, title="ANARCI Comparison")
    scfv.html_title(outfile_html, "ANARCI Comparison Results")

    # Consensus
    scfv.html_subtitle(outfile_html, "Consensus Heavy-Chain Sequences")
    scfv.show_anarci_html("../example_data/consensus_H_1_0.csv",
                        outfile=outfile_html, number=True, chain="H",
                        legend=True, region="ALL", show_header=True)

    scfv.show_anarci_html("../example_data/consensus_H_0_0.csv",
                        outfile=outfile_html, number=False, chain="H",
                        legend=False, region="ALL", show_header=False)

    scfv.show_anarci_html("../example_data/diff_H.csv",
                        outfile=outfile_html, number=False, chain="H",
                        legend=False, region="ALL", show_header=False)


    # Final scored designs
    scfv.show_anarci_html(args.out,
                          outfile=outfile_html, number=False, chain="H", legend=False, region="ALL", show_header=True)

    scfv.html_end(outfile_html)

    # Terminal output versions
    scfv.show_anarci_csv("../example_data/consensus_H_1_0.csv",
                        number=True, chain="H", legend=True, region="ALL", show_header=True)

    scfv.show_anarci_csv("../example_data/consensus_H_0_0.csv",
                        number=False, chain="H", legend=False, region="ALL", show_header=False)

    scfv.show_anarci_csv("../example_data/diff_H.csv",
                        number=False, chain="H", legend=False, region="ALL", show_header=False)

    scfv.show_anarci_csv(args.out,
                         number=False, chain="H", legend=False, region="ALL", show_header=True)


if __name__ == "__main__":
    main()
