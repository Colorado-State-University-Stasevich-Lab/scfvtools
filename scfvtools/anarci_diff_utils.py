import pandas as pd
import re
import os


import pandas as pd
import re
import os


def make_diff_df(df1, name1, df2, name2, outfile="auto"):
    """
    Compare two ANARCI-style dataframes and generate a DIFF dataframe.

    NEW unified DIFF logic (no DIFF+ or DIFF-):

      - aa1 == aa2 → diff_aa = "-"       diff_region = "DIFF0"

      - aa1 != aa2:
            diff_aa = aa1 if aa1 != "-" else aa2
            diff_region = f"DIFF({aa1}{aa2})"

      This works for:
          (X, -) → DIFF(X-)
          (-, Y) → DIFF(-Y)
          (X, Y) → DIFF(XY)

    Always uses DIFF(XY) format to ensure consistency.
    """

    # ------------------------------------------------------------
    # Extract relevant sequences
    # ------------------------------------------------------------
    seq1 = df1[df1["name"] == name1].copy()
    seq2 = df2[df2["name"] == name2].copy()

    if seq1.empty:
        raise ValueError(f"Sequence '{name1}' not found in df1.")
    if seq2.empty:
        raise ValueError(f"Sequence '{name2}' not found in df2.")

    pos1 = seq1["position"].astype(str).unique()
    pos2 = seq2["position"].astype(str).unique()
    all_positions = sorted(set(pos1) | set(pos2), key=_pos_sort_key)

    map1 = {str(r["position"]): r["aa"] for _, r in seq1.iterrows()}
    map2 = {str(r["position"]): r["aa"] for _, r in seq2.iterrows()}

    scheme_used = seq1["scheme"].iloc[0]
    chain_used = seq1["chain"].iloc[0]

    base_name = os.path.basename(outfile).replace(".csv", "") if outfile != "auto" else None

    out_rows = []

    # ------------------------------------------------------------
    # Build DIFF rows (UNIFIED NEW LOGIC)
    # ------------------------------------------------------------
    for pos in all_positions:
        aa1 = map1.get(pos, "-")
        aa2 = map2.get(pos, "-")

        if aa1 == aa2:
            diff_aa = "-"
            diff_region = "DIFF0"

        else:
            # DIFFERENT: always DIFF(XY)
            diff_aa = aa1 if aa1 != "-" else aa2
            diff_region = f"DIFF({aa1}{aa2})"

        out_rows.append({
            "name": base_name if base_name else f"diff_{name1}_{name2}",
            "position": pos,
            "chain": chain_used,
            "aa": diff_aa,
            "Region": diff_region,
            "scheme": scheme_used,
            "seq1": aa1,
            "seq2": aa2,
        })

    diff_df = pd.DataFrame(out_rows)

    # ------------------------------------------------------------
    # Auto outfile format
    # ------------------------------------------------------------
    if outfile == "auto":
        safe1 = re.sub(r"[^A-Za-z0-9]+", "_", name1)
        safe2 = re.sub(r"[^A-Za-z0-9]+", "_", name2)
        outfile = f"diff_{safe1}_vs_{safe2}.csv"

    # Write CSV
    if outfile:
        diff_df.to_csv(outfile, index=False)

    return diff_df


def _pos_sort_key(p):
    p = str(p)
    num = ''.join(c for c in p if c.isdigit())
    let = p[len(num):]
    return (int(num), let)
