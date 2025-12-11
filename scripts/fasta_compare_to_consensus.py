from pathlib import Path
import argparse
import scfvtools as scfv

def main():
    parser = argparse.ArgumentParser(
        description=(
            "scFv FASTA + consensus df (csv)"
            "→ scoring of scFv sequences"
        )
    )

    parser.add_argument("--ref_csv", required=True,
                        help="Path to reference consensus CSV (e.g. diff_H.csv)")
    parser.add_argument("--name", required=True,
                        help="Name of consensus sequence in reference")
    parser.add_argument("--data_fasta", required=True,
                        help="FASTA containing the sequences you want to score")
    parser.add_argument("--out", required=True,
                        help="Output CSV path for scored sequences")

    args = parser.parse_args()

    print(f"[INFO] Running make_score_df with:")
    print(f"       ref_csv/ = {args.ref_csv}")
    print(f"       name1   = {args.name}")
    print(f"       data_fasta = {args.data_fasta}")
    print(f"       outfile = {args.out}")

    df = scfv.anarci_to_dataframe(
        input_fasta=args.data_fasta,
        scheme="martin"
    )
    # Turn input fasta path into a pathlib object
    inpath = Path(args.data_fasta)
    # Replace extension with .csv
    outfile = Path("../output_dir") / inpath.with_suffix(".csv").name

    # Save to same directory as the FASTA
    df.to_csv(outfile, index=False)

    score_df = scfv.make_score_df(
        ref_csv=args.ref_csv,
        name1=args.name,
        data_csv=outfile,
        outfile=args.out
    )

    print(f"[INFO] Score dataframe written to: {args.out}")

    # Optional display of ANARCI heatmap/HTML
    print("[INFO] Displaying alignment (H chain)...")
    # -------------------------------
    # START HTML
    # -------------------------------
    outfile2 = Path("../output_dir") / inpath.with_suffix(".html").name
    scfv.html_start(outfile2, title="ANARCI Comparison")
    scfv.html_title(outfile2, "ANARCI Comparison Results")
    # -------------------------------
    # CONSENSUS SECTION
    # -------------------------------
    scfv.html_subtitle(outfile2, "Consensus Heavy-Chain Sequences")
    scfv.show_anarci_html("../output_dir/consensus_csv/consensus_H_1_0.csv",
                        outfile=outfile2, number=True, chain="H", legend=True, region="ALL", show_header=True)
    scfv.show_anarci_html("../output_dir/consensus_csv/consensus_H_0_0.csv",
                        outfile=outfile2, number=False, chain="H", legend=False, region="ALL", show_header=False)
    scfv.show_anarci_html("../output_dir/consensus_csv/diff_H.csv",
                        outfile=outfile2, number=False, chain="H", legend=False, region="ALL", show_header=False)
    # -------------------------------
    # FINAL DESIGNS / SCORE SECTION
    # -------------------------------
    scfv.show_anarci_html(args.out,
                        outfile=outfile2, number=False, chain="H", legend=False, region="ALL", show_header=True)
    scfv.html_end(outfile2)

    # -------------------------------
    # TERMINAL OUTPUT
    # -------------------------------
    scfv.show_anarci_csv("../output_dir/consensus_csv/consensus_H_1_0.csv", number=True, chain="H", legend=True, region="ALL", show_header=True)
    scfv.show_anarci_csv("../output_dir/consensus_csv/consensus_H_0_0.csv", number=False, chain="H", legend=False, region="ALL", show_header=False)
    scfv.show_anarci_csv("../output_dir/consensus_csv/diff_H.csv", number=False, chain="H", legend=False, region="ALL", show_header=False)
    scfv.show_anarci_csv(args.out, number=False, chain="H", legend=False, region="ALL", show_header=True)

if __name__ == "__main__":
    main()
