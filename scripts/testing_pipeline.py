import argparse
import scfvtools as scfv


def main():
    parser = argparse.ArgumentParser(
        description=(
            "Excel scFv spreadsheet → FASTA → ANARCI alignment → Consensus pipeline "
            "→ scoring of new sequences"
        )
    )
    #Run this to test: python testing_pipeline.py --ref_csv ../output_dir/consensus_csv/diff_H.csv --name "diff_H" --data_csv ../output_dir/8wg16dA_MPNN_designs_chainA_only.csv --out ../output_dir/consensus_csv/8wg16dA_MPNN_designs_scores.csv
    parser.add_argument("--ref_csv", required=True,
                        help="Path to reference consensus CSV (e.g. diff_H.csv)")
    parser.add_argument("--name", required=True,
                        help="Name to assign to this comparison set (e.g. diff_H)")
    parser.add_argument("--data_csv", required=True,
                        help="CSV containing the sequences you want to score")
    parser.add_argument("--out", required=True,
                        help="Output CSV path for scored sequences")

    args = parser.parse_args()

    print(f"[INFO] Running make_score_df with:")
    print(f"       ref_csv = {args.ref_csv}")
    print(f"       data_csv = {args.data_csv}")
    print(f"       outfile = {args.out}")

    score_df = scfv.make_score_df(
        ref_csv=args.ref_csv,
        name1=args.name,
        data_csv=args.data_csv,
        outfile=args.out
    )

    print(f"[INFO] Score dataframe written to: {args.out}")

    # Optional display of ANARCI heatmap/HTML
    print("[INFO] Displaying alignment (H chain)...")
    # -------------------------------
    # START HTML
    # -------------------------------
    scfv.html_start("../output_dir/test.html", title="ANARCI Comparison")
    scfv.html_title("../output_dir/test.html", "ANARCI Comparison Results")
    # -------------------------------
    # CONSENSUS SECTION
    # -------------------------------
    scfv.html_subtitle("../output_dir/test.html", "Consensus Heavy-Chain Sequences")
    scfv.show_anarci_html("../output_dir/consensus_csv/consensus_H_1_0.csv",
                        outfile="../output_dir/test.html", number=True, chain="H", legend=True, region="ALL", show_header=True)
    scfv.show_anarci_html("../output_dir/consensus_csv/consensus_H_0_0.csv",
                        outfile="../output_dir/test.html", number=False, chain="H", legend=False, region="ALL", show_header=False)
    scfv.show_anarci_html("../output_dir/consensus_csv/diff_H.csv",
                        outfile="../output_dir/test.html", number=False, chain="H", legend=False, region="ALL", show_header=False)
    # -------------------------------
    # FINAL DESIGNS / SCORE SECTION
    # -------------------------------
    # scfv.html_subtitle("../output_dir/test.html", "Final Designed Sequences (score.csv)")
    scfv.show_anarci_html("../output_dir/score.csv",
                        outfile="../output_dir/test.html", number=False, chain="H", legend=False, region="ALL", show_header=True)
    scfv.html_end("../output_dir/test.html")

    # -------------------------------
    # TERMINAL OUTPUT
    # -------------------------------
    scfv.show_anarci_csv("../output_dir/consensus_csv/consensus_H_1_0.csv", number=True, chain="H", legend=True, region="ALL", show_header=True)
    scfv.show_anarci_csv("../output_dir/consensus_csv/consensus_H_0_0.csv", number=False, chain="H", legend=False, region="ALL", show_header=False)
    scfv.show_anarci_csv("../output_dir/consensus_csv/diff_H.csv", number=False, chain="H", legend=False, region="ALL", show_header=False)
    scfv.show_anarci_csv("../output_dir/score.csv", number=False, chain="H", legend=False, region="ALL", show_header=True)

if __name__ == "__main__":
    main()