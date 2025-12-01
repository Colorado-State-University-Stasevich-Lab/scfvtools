import pandas as pd
from collections import Counter, defaultdict
import os
import re

# ------------------------------------------------------------
# MAIN CONSENSUS FUNCTION (FRAMEWORK ONLY)
# ------------------------------------------------------------
def build_framework_consensus(df, threshold=0.6, df_source=None):
    """
    Build framework-only consensus sequences from the ANARCI dataframe.
    NO PRINTING — only computation and writing CSV outputs.
    """

    # ------------------------------------------------------------
    # 1. Remove CDR rows
    # ------------------------------------------------------------
    df = df[df["Region"].str.startswith("FR")].copy()

    # ------------------------------------------------------------
    # 2. Identify annotation columns (example: hit/miss)
    # ------------------------------------------------------------
    fixed_cols = {"name", "position", "chain", "aa", "Region", "scheme"}
    annotation_cols = [c for c in df.columns if c not in fixed_cols]

    # Normalize annotation columns
    for ann_col in annotation_cols:
        df[ann_col] = pd.to_numeric(df[ann_col], errors="coerce").fillna(0.0)

    # ------------------------------------------------------------
    # 3. Region map (pos → FR1/FR2/FR3/FR4)
    # ------------------------------------------------------------
    region_map = {}
    for _, row in df.iterrows():
        region_map[str(row["position"])] = row["Region"]

    # ------------------------------------------------------------
    # 4. Sort ANARCI positions
    # ------------------------------------------------------------
    def pos_sort_key(p):
        p = str(p)
        num = ''.join(c for c in p if c.isdigit())
        let = p[len(num):]
        return (int(num), let)

    positions = sorted(df["position"].unique(), key=pos_sort_key)

    # ------------------------------------------------------------
    # 5. Prepare output directory
    # ------------------------------------------------------------
    out_dir = "consensus_csv"
    os.makedirs(out_dir, exist_ok=True)

    # ------------------------------------------------------------
    # 6. Build consensus sequences
    # ------------------------------------------------------------
    results = {}

    scheme_used = df["scheme"].iloc[0] if "scheme" in df.columns else "unknown"

    for chain_type in sorted(df["chain"].unique()):
        chain_df = df[df["chain"] == chain_type]
        results[chain_type] = {}

        for ann_col in annotation_cols:
            for ann_value in sorted(chain_df[ann_col].unique()):

                subset = chain_df[chain_df[ann_col] == ann_value]

                # Gather residues per position
                pos_to_aa = defaultdict(list)
                for _, row in subset.iterrows():
                    pos_to_aa[str(row["position"])].append(row["aa"])

                consensus = []
                regions = []

                for pos in positions:
                    p = str(pos)
                    region = region_map[p]
                    aas = pos_to_aa.get(p, [])

                    if not aas:
                        consensus.append("-")
                        regions.append(region)
                        continue

                    top_aa, top_count = Counter(aas).most_common(1)[0]
                    frac = top_count / len(aas)

                    consensus.append(top_aa if frac >= threshold else "-")
                    regions.append(region)

                raw_seq = "".join(consensus)
                results[chain_type][(ann_col, ann_value)] = raw_seq

                # ------------------------------------------------------------
                # 7. Write consensus CSV
                # ------------------------------------------------------------
                out_rows = []
                for pos, aa, region in zip(positions, consensus, regions):
                    out_rows.append({
                        "name": f"consensus_{chain_type}",
                        "position": pos,
                        "chain": chain_type,
                        "aa": aa,
                        "Region": region,
                        "scheme": scheme_used,
                        ann_col: ann_value,
                    })

                out_df = pd.DataFrame(out_rows)

                # sanitize value for filename
                safe_value = re.sub(r"[^A-Za-z0-9]+", "_", str(ann_value))
                csv_path = f"{out_dir}/consensus_{chain_type}_{safe_value}.csv"
                out_df.to_csv(csv_path, index=False)

    return results
