#!/usr/bin/env python3
import argparse
from scfvtools.io_utils import read_excel_to_fasta
from scfvtools.anarci_utils import run_anarci_and_align_fasta


def main():
    parser = argparse.ArgumentParser(
        description="Excel → FASTA → ANARCI pipeline (all outputs saved)."
    )

    parser.add_argument("--excel", required=True, help="Path to Excel file")
    parser.add_argument("--name", required=True, help="Column containing names")
    parser.add_argument("--seq", required=True, help="Column containing sequences")
    parser.add_argument("--out-fasta", required=True,
                        help="Output FASTA created from Excel")
    parser.add_argument("--aligned", required=True,
                        help="Output FASTA after ANARCI alignment")
    parser.add_argument("--contains", help="Substring filter for names", default=None)
    parser.add_argument("--scheme", default="martin",
                        help="ANARCI numbering scheme")

    args = parser.parse_args()

    print("STEP 1: Reading Excel → Writing FASTA")
    records = read_excel_to_fasta(
        excel_path=args.excel,
        name_column=args.name,
        sequence_column=args.seq,
        output_fasta=args.out_fasta,
        contains_string=args.contains,
    )

    print(f"✔ Wrote {len(records)} sequences → {args.out_fasta}")

    print("\nSTEP 2: Running ANARCI alignment…")
    run_anarci_and_align_fasta(
        input_fasta=args.out_fasta,
        output_fasta=args.aligned,
        scheme=args.scheme,
    )

    print(f"\n✔ Final aligned FASTA written → {args.aligned}")
    print("\nPipeline complete.")


if __name__ == "__main__":
    main()
