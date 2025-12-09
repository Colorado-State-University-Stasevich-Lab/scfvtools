import pandas as pd
import os
import re

def pos_sort_key(p):
    """
    Sort ANARCI positions correctly:
    12, 12A, 12B, 13, ...
    """
    p = str(p)
    num = ''.join(c for c in p if c.isdigit())
    let = p[len(num):]
    return (int(num), let)


# =====================================================================================
# MAIN FUNCTION: COMPARE ALL SEQUENCES IN data_csv TO A SINGLE REFERENCE
# =====================================================================================
def make_score_df(ref_csv, name1, data_csv, outfile=None):
    """
    Compare a SINGLE reference sequence (ref_csv) to ALL sequences in data_csv.

    Logic:
      • Output AA is always **data AA**
      • Region ALWAYS comes from reference Region column
      • Score = (# DIFF+ positions) - (# DIFF- positions)

    Region interpretation:
      • If Region == "DIFF0": always DIFF0
      • If Region == "DIFF(XY)":
            If data AA == X → region = DIFF+
            elif data AA == Y → region = DIFF-
            else → region = DIFF0

    Only positions where chain matches reference chain are compared.

    Returns a DataFrame and optionally writes CSV.
    """

    # -------------------------------------------------------------------------
    # Load reference — must contain ONE sequence
    # -------------------------------------------------------------------------
    ref_df = pd.read_csv(ref_csv)
    if len(ref_df['name'].unique()) != 1:
        raise ValueError("Reference CSV must contain exactly ONE sequence.")

    # Determine chain to compare
    ref_chain = ref_df['chain'].iloc[0]

    # Map: position → (ref_aa, ref_region)
    ref_map = {
        (row['position']): (row['aa'], str(row['Region']))
        for _, row in ref_df.iterrows()
    }

    ref_positions_sorted = sorted(ref_map.keys(), key=pos_sort_key)

    # -------------------------------------------------------------------------
    # Load data: contains MANY sequences
    # -------------------------------------------------------------------------
    data_df = pd.read_csv(data_csv)

    # Filter to only matching chain
    data_df = data_df[data_df['chain'] == ref_chain].copy()

    # Preserve NAME order as they appear in CSV
    seq_order = data_df['name'].drop_duplicates().tolist()

    out_rows = []

    # -------------------------------------------------------------------------
    # For each sequence in original order
    # -------------------------------------------------------------------------
    for seq_name in seq_order:

        seq_group = data_df[data_df["name"] == seq_name]

        # Build mapping position → data AA
        data_map = {
            row['position']: row['aa']
            for _, row in seq_group.iterrows()
        }

        score_green = 0
        score_red = 0

        # Process all reference positions in sorted order
        for pos in ref_positions_sorted:

            ref_aa, ref_region = ref_map[pos]
            data_aa = data_map.get(pos, "-")

            # -------------------------------------------
            # Region propagation logic
            # -------------------------------------------
            out_region = "DIFF0"  # default (same AA OR neutral fallback)

            if ref_region == "DIFF0":
                out_region = "DIFF0"

            elif ref_region.startswith("DIFF(") and ref_region.endswith(")"):
                inside = ref_region[len("DIFF("):-1]  # extract XY inside DIFF(XY)

                if len(inside) == 2:
                    X, Y = inside[0], inside[1]

                    if data_aa == X:
                        out_region = "DIFF+"
                        score_green += 1

                    elif data_aa == Y:
                        out_region = "DIFF-"
                        score_red += 1

                    else:
                        # NEW: Neither X nor Y → ambiguous → DIFF?
                        out_region = "DIFF?"

                else:
                    # malformed DIFF tag safety
                    out_region = "DIFF0"

            else:
                # Should not occur anymore, fallback
                out_region = "DIFF0"


            # Output AA always = DATA AA
            out_rows.append({
                "name": seq_name,
                "position": pos,
                "chain": ref_chain,
                "aa": data_aa,
                "Region": out_region,
                "reference": name1,
                "Score": None  # fill later
            })

        # Fill score for all rows of this sequence
        final_score = score_green - score_red
        for row in out_rows:
            if row["name"] == seq_name:
                row["Score"] = final_score

    # -------------------------------------------------------------------------
    # Convert to DataFrame
    # -------------------------------------------------------------------------
    out_df = pd.DataFrame(out_rows)

    # -------------------------------------------------------------------------
    # Write output file (preserve directory behavior)
    # -------------------------------------------------------------------------
    if outfile is not None:
        out_dir = os.path.dirname(outfile)
        if out_dir not in ("", "."):
            os.makedirs(out_dir, exist_ok=True)
        out_df.to_csv(outfile, index=False)

    return out_df
