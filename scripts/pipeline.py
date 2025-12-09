#!/usr/bin/env python3
import argparse
import pandas as pd
import scfvtools as scfv




def main():
    parser = argparse.ArgumentParser(
        description="Excel scFv spreadsheet → FASTA files for scfvs → ANARCI alignment → Consensus pipeline for scfv sequences"
    )

    parser.add_argument("--excel", required=True, help="Path to Excel file with scfv sequences")
    parser.add_argument("--name", required=True, help="Header for column containing names of scFvs")
    parser.add_argument("--seq", required=True, help="Header for column containing aa sequences")

    parser.add_argument("--raw", required=True,
                        help="Output FASTA file (unaligned raw sequences)")
    parser.add_argument("--out", required=True,
                        help="Output aligned FASTA file (anarci numbering by scheme)")

    parser.add_argument("--consensus", required=True,
                        help="Output consensus FASTA file")

    parser.add_argument("--contains", help="Substring filter (optional)")
    parser.add_argument("--scheme", default="martin",
                        help="ANARCI numbering scheme")
    parser.add_argument("--threshold", type=float, default=0.6,
                        help="Consensus aa frequency threshold (0–1)")
    parser.add_argument(
        "--annotate",
        help="Comma-separated list of extra Excel columns to append to FASTA headers"
    )

    args = parser.parse_args()
    annotation_columns = None

    if args.annotate:
        annotation_columns = [c.strip() for c in args.annotate.split(",")]


    # ------------------------------------------------------------
    # Auto-create directories for user output paths
    # ------------------------------------------------------------
    import os
    def ensure_parent_dir(path):
        parent = os.path.dirname(os.path.abspath(path))
        if parent and not os.path.exists(parent):
            os.makedirs(parent, exist_ok=True)

    # Create parent dirs for raw FASTA, aligned FASTA, and consensus FASTA
    ensure_parent_dir(args.raw)
    ensure_parent_dir(args.out)
    ensure_parent_dir(args.consensus)


    # ------------------------------------------------------------
    # STEP 1: Read Excel → FASTA
    # ------------------------------------------------------------
    print("STEP 1: Reading Excel and writing raw FASTA...")

    records = scfv.read_excel_to_fasta(
        excel_path=args.excel,
        name_column=args.name,
        sequence_column=args.seq,
        output_fasta=args.raw,
        contains_string=args.contains,
        annotation_columns=annotation_columns
    )
    print(f"✔ Wrote {len(records)} sequences → {args.raw}")

    # ------------------------------------------------------------
    # STEP 1: Build per-residue DataFrame with Region / CDR / FR
    # ------------------------------------------------------------
    from scfvtools.anarci_utils import anarci_to_dataframe

    print("STEP 2: Creating residue-level annotation dataframe (Region, scheme, annotations)...")
    df = scfv.anarci_to_dataframe(
        input_fasta=args.raw,
        scheme=args.scheme,
    )

    # Output CSV next to aligned FASTA
    df_out = args.out + ".csv"
    df.to_csv(df_out, index=False)
    print(f"✔ Annotation table written → {df_out}")


    # ------------------------------------------------------------
    # STEP 3: Build framework consensus sequences (color-coded)
    # ------------------------------------------------------------
    print("\nSTEP 3: Building framework consensus sequences...")

    import os 

    # Load residue-level annotation table created in Step 2
    df_path = args.out + ".csv"
    if not os.path.exists(df_path):
        raise FileNotFoundError(f"Expected annotation CSV not found: {df_path}")

    df = pd.read_csv(df_path)

    # Run consensus builder (prints alignment to screen + writes CSVs)
    _ = scfv.build_framework_consensus(
            df,
            threshold=args.threshold,
            df_source=df_path
        )

    scfv.show_anarci_csv("../output_dir/consensus_csv/consensus_H_0_0.csv", number=True, legend=True, region="ALL")
    scfv.show_anarci_csv("../output_dir/consensus_csv/consensus_H_1_0.csv", number=False, legend=False, region="ALL")
    scfv.show_anarci_csv("../output_dir/consensus_csv/consensus_K_0_0.csv", number=False, legend=False, region="ALL")
    scfv.show_anarci_csv("../output_dir/consensus_csv/consensus_K_1_0.csv", number=False, legend=False, region="ALL")

    # ------------------------------------------------------------
    # STEP 4: Compute differences between consensus groups
    # ------------------------------------------------------------
    print("STEP 4: Computing consensus differences...")

    # Paths to consensus files
    c0_path = "../output_dir/consensus_csv/consensus_H_0_0.csv"
    c1_path = "../output_dir/consensus_csv/consensus_H_1_0.csv"

    # Load the consensus dataframes
    c0 = pd.read_csv(c0_path)
    c1 = pd.read_csv(c1_path)

    # Compute diff dataframe
    diff_df = scfv.make_diff_df(
        df1=c1,
        name1="consensus_H",
        df2=c0,
        name2="consensus_H",
        outfile="../output_dir/consensus_csv/diff_H.csv"
    )

    print("✔ Diff written → diff_H.csv\n")

    # OPTIONAL: display diff with color and numbering
    print("DIFF VIEW:")
    scfv.show_anarci_csv("../output_dir/consensus_csv/consensus_H_1_0.csv", number=True, legend=True, region="ALL")
    scfv.show_anarci_csv("../output_dir/consensus_csv/consensus_H_0_0.csv", number=False, legend=False, region="ALL")
    scfv.show_anarci_csv("../output_dir/consensus_csv/diff_H.csv", number=False, legend=False, region="ALL")

    # ------------------------------------------------------------
    # STEP 5: Score sequences
    # ------------------------------------------------------------

    df = scfv.anarci_to_dataframe(
        input_fasta="../example_data/8wg16dA_MPNN_designs_chainA_only.fasta",
        scheme="martin"
    )
    # Output CSV next to aligned FASTA
    df.to_csv("../output_dir/8wg16dA_MPNN_designs_chainA_only.csv", index=False)

    score_df = scfv.make_score_df(
        ref_csv="../output_dir/consensus_csv/diff_H.csv",
        name1="diff_H",
        data_csv="../output_dir/8wg16dA_MPNN_designs_chainA_only.csv",
        outfile="../output_dir/consensus_csv/8WG16dA.csv"
    )
    scfv.show_anarci_csv("../output_dir/consensus_csv/8WG16dA.csv", number=False, legend=False, region="ALL", chain="H")
    #show_anarci_csv("output_dir/aligned_output.fasta.csv", number=True, legend=False, region="ALL", chain="H")

if __name__ == "__main__":
    main()
