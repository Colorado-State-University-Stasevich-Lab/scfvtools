import re
import pandas as pd
from Bio import SeqIO
from anarci import run_anarci

CDR_MAP = {
    "kabat":   {"H1": (30, 35), "H2": (50, 65), "H3": (95, 102),
                "L1": (24, 34), "L2": (50, 56), "L3": (89, 97)},
    "chothia": {"H1": (26, 32), "H2": (52, 56), "H3": (95, 102),
                "L1": (26, 32), "L2": (50, 52), "L3": (91, 96)},
    "martin":  {"H1": (30, 35), "H2": (47, 58), "H3": (95, 101),
                "L1": (30, 35), "L2": (46, 55), "L3": (89, 97)},
    "imgt":    {"H1": (27, 38), "H2": (56, 65), "H3": (105, 117),
                "L1": (27, 38), "L2": (56, 65), "L3": (105, 117)},
    "aho":     {"H1": (25, 40), "H2": (58, 77), "H3": (109, 137),
                "L1": (25, 40), "L2": (58, 77), "L3": (109, 137)},
}


def anarci_to_dataframe(input_fasta, scheme="martin"):
    """
    Run ANARCI on each sequence in a FASTA file and output a per-position dataframe.

    Columns include:
        name | position | chain | aa | Region | scheme | <annotations>
    """

    records = list(SeqIO.parse(input_fasta, "fasta"))
    if not records:
        raise ValueError("No sequences found in FASTA")

    scheme_key = scheme.lower()
    if scheme_key not in CDR_MAP:
        raise ValueError(f"Unknown scheme '{scheme}' (must be one of {list(CDR_MAP.keys())})")

    seq_pairs = [(rec.id, str(rec.seq)) for rec in records]

    sequences, numbering, alignment_details, hmmer_table = run_anarci(
        seq_pairs, scheme=scheme
    )

    rows = []

    # --------------------------------------------
    # Extract annotations like "hit/miss=1.0"
    # --------------------------------------------
    def parse_annotations(header):
        annotations = {}
        parts = header.split("|")
        for p in parts[1:]:
            if "=" in p:
                key, val = p.split("=", 1)
                annotations[key] = val
        return annotations

    # --------------------------------------------
    # Determine FR/CDR region for a given chain + position
    # --------------------------------------------
    def classify_region(chain, pos_int):
        """Returns FR1/2/3/4 or CDR1/2/3 based on numeric pos_int."""
        cdrs = CDR_MAP[scheme_key]

        if chain == "H":
            boundaries = cdrs["H1"], cdrs["H2"], cdrs["H3"]
        elif chain in ("K", "L"):
            boundaries = cdrs["L1"], cdrs["L2"], cdrs["L3"]
        else:
            return "UNK"

        (c1_start, c1_end), (c2_start, c2_end), (c3_start, c3_end) = boundaries

        if c1_start <= pos_int <= c1_end:
            return "CDR1"
        elif c2_start <= pos_int <= c2_end:
            return "CDR2"
        elif c3_start <= pos_int <= c3_end:
            return "CDR3"
        elif pos_int < c1_start:
            return "FR1"
        elif pos_int > c1_end and pos_int < c2_start:
            return "FR2"
        elif pos_int > c2_end and pos_int < c3_start:
            return "FR3"
        elif pos_int > c3_end:
            return "FR4"
        return "UNK"


    # --------------------------------------------
    # Expand ANARCI result into dataframe rows
    # --------------------------------------------
    for (header, seq), chain_numberings, chain_info in zip(
        sequences, numbering, alignment_details
    ):
        if chain_numberings is None:
            print(f"[WARNING] ANARCI failed on sequence: {header}")
            continue

        name = header
        annotations = parse_annotations(header)

        for dom_idx, domain in enumerate(chain_numberings):
            if domain is None:
                continue

            numbering_data, start_pos, end_pos = domain
            chain_type = chain_info[dom_idx].get("chain_type", "UNK")

            pos_to_aa = {}
            positions = []

            # Collect ANARCI positions like 1, 2, ..., 72A, 72B
            for (pos_tuple, aa) in numbering_data:
                pos_raw, letter = pos_tuple            # e.g. (72, 'A')
                pos_str = f"{pos_raw}{letter}"         # → "72A"
                pos_to_aa[pos_str] = aa
                positions.append(pos_str)


            # Sort positions: 1,2,...,72A,72B
            def sort_key(x):
                m = re.match(r"(\d+)([A-Z]?)", x)
                if m:
                    return (int(m.group(1)), m.group(2))
                return (9999, x)

            positions = sorted(positions, key=sort_key)

            # Add dataframe rows
            for pos_str in positions:
                # numeric portion for region assignment
                m = re.match(r"(\d+)", pos_str)
                pos_int = int(m.group(1)) if m else None

                region = classify_region(chain_type, pos_int) if pos_int else "UNK"

                rows.append({
                    "name": name,
                    "position": pos_str,
                    "chain": chain_type,
                    "aa": pos_to_aa.get(pos_str, "-"),
                    "Region": region,              # NEW
                    "scheme": scheme_key,          # NEW
                    **annotations
                })

    return pd.DataFrame(rows)
