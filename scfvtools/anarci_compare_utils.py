import pandas as pd
import os
import re
from Bio.Align import substitution_matrices

def pos_sort_key(p):
    """
    Sort ANARCI positions correctly:
    12, 12A, 12B, 13, ...
    """
    p = str(p)
    num = ''.join(c for c in p if c.isdigit())
    let = p[len(num):]
    return (int(num), let)



# Canonical AA alphabet used for normalization
AA20 = list("ARNDCQEGHILKMFPSTWYV")


def _load_subst_matrix(matrix_name: str = "BLOSUM62"):
    # Biopython substitution matrices (e.g., BLOSUM62, BLOSUM80, PAM250)
    return substitution_matrices.load(matrix_name)


def _mat_score(mat, a: str, b: str):
    # Biopython matrix supports indexing as mat[a, b]; be robust to ordering
    try:
        return float(mat[a, b])
    except Exception:
        try:
            return float(mat[b, a])
        except Exception:
            return None


def _make_blosum_normalizer(mat):
    """
    Returns a function penalty(ref_aa, data_aa) -> float in [-1, 0].

    Normalization per reference residue:
      - identical => 0
      - worst substitution (for that ref_aa) => -1
      - intermediate substitutions interpolated in between
    """
    best = {}
    worst = {}

    for r in AA20:
        vals = [_mat_score(mat, r, x) for x in AA20]
        vals = [v for v in vals if v is not None]
        if not vals:
            # Extremely defensive fallback; shouldn't happen for BLOSUM62
            best[r] = 0.0
            worst[r] = -1.0
        else:
            best[r] = _mat_score(mat, r, r)
            worst[r] = min(vals)

    def penalty(
        ref_aa: str,
        data_aa: str,
        *,
        gap_penalty: float = -1.0,
        unknown_penalty: float = -1.0,
    ) -> float:
        if data_aa in ("-", None) or (isinstance(data_aa, float) and pd.isna(data_aa)):
            return float(gap_penalty)

        # Only normalize against canonical AA20; treat others (X, B, Z, *, etc.) as unknown
        if ref_aa not in best or data_aa not in AA20:
            return float(unknown_penalty)

        if data_aa == ref_aa:
            return 0.0

        s = _mat_score(mat, ref_aa, data_aa)
        if s is None:
            return float(unknown_penalty)

        denom = (best[ref_aa] - worst[ref_aa])
        if denom == 0:
            return -1.0

        # in [-1, 0]
        return - (best[ref_aa] - s) / denom

    return penalty


# =====================================================================================
# MAIN FUNCTION: COMPARE ALL SEQUENCES IN data_csv TO A SINGLE REFERENCE
# =====================================================================================
def make_score_df(
    ref_csv,
    name1,
    data_csv,
    outfile=None,
    gap_penalty: float = -1.0,
    unknown_penalty: float = -1.0,
    matrix_name: str = "BLOSUM62",
):
    """
    Compare a SINGLE reference DIFF table (ref_csv) to ALL sequences in data_csv.

    The reference CSV is expected to contain per-position rows with:
      - position, chain, aa (displayed reference residue), Region
    where Region may encode preference sites as DIFF(XY):
      - X = preferred residue ("green")
      - Y = dispreferred residue ("red")

    Scoring scope (per position):
      A position is eligible for scoring only if:
        1) displayed reference aa is not "-" / blank / NaN, and
        2) Region is of the form DIFF(XY) with exactly 2 characters inside.
      Otherwise the position contributes 0 and is labeled DIFF0.

    Per-sequence outputs (totals are repeated on every row for that sequence):
      - Score (hard):
          DIFF+ if data_aa == X  -> +1
          DIFF- if data_aa == Y  -> -1
          DIFF? otherwise        ->  0
        Score = (#DIFF+) - (#DIFF-)

      - BLOSUM DIFF SCORE (soft, discriminative):
        For each eligible DIFF(XY) site:
          sx = sim(data_aa, X)
          sy = sim(data_aa, Y)
        BLOSUM DIFF SCORE = Σ (sx - sy)

      - BLOSUM SCORE (soft, preference with sign):
        For each eligible DIFF(XY) site:
          sx = sim(data_aa, X)
          sy = sim(data_aa, Y)
          add +sx if sx > sy
          add -sy if sy > sx
          add  0  if sx == sy

    Similarity definition:
      sim(a, b) returns a value in [0, 1] derived from a normalized substitution
      penalty p in [-1, 0] (default: BLOSUM62):
        sim = clamp(1 + p, 0, 1)
      Gaps ("-") in either argument yield sim = 0.

    Notes:
      - DIFF0 positions never contribute to either soft score.
      - If X or Y is "-", sim(..., "-") = 0, so such sites cannot contribute.
    """
    ref_df = pd.read_csv(ref_csv)
    if len(ref_df["name"].unique()) != 1:
        raise ValueError("Reference CSV must contain exactly ONE sequence.")
    ref_chain = ref_df["chain"].iloc[0]

    # Map: position → (ref_aa, ref_region)
    ref_map = {row["position"]: (row["aa"], str(row["Region"])) for _, row in ref_df.iterrows()}
    ref_positions_sorted = sorted(ref_map.keys(), key=pos_sort_key)

    # BLOSUM setup (normalized penalties in [-1, 0])
    blosum_mat = _load_subst_matrix(matrix_name)
    blosum_penalty = _make_blosum_normalizer(blosum_mat)

    def is_scored_ref_aa(ref_aa) -> bool:
        """Only score positions where the displayed reference AA is not '-' (or blank/NaN)."""
        if ref_aa is None:
            return False
        if isinstance(ref_aa, float) and pd.isna(ref_aa):
            return False
        return str(ref_aa).strip() not in ("", "-")

    def sim(data_aa: str, target_aa: str) -> float:
        """Similarity in [0,1] derived from normalized BLOSUM penalty in [-1,0]."""
        data_aa = str(data_aa).strip()
        target_aa = str(target_aa).strip()
        if data_aa == "-" or target_aa == "-":
            return 0.0

        p = blosum_penalty(
            target_aa,
            data_aa,
            gap_penalty=gap_penalty,
            unknown_penalty=unknown_penalty,
        )
        s = 1.0 + float(p)  # p in [-1,0] -> s in [0,1]
        if s < 0.0:
            return 0.0
        if s > 1.0:
            return 1.0
        return s

    # Load data
    data_df = pd.read_csv(data_csv)
    data_df = data_df[data_df["chain"] == ref_chain].copy()
    seq_order = data_df["name"].drop_duplicates().tolist()

    out_rows = []

    for seq_name in seq_order:
        seq_group = data_df[data_df["name"] == seq_name]
        data_map = {row["position"]: row["aa"] for _, row in seq_group.iterrows()}

        score_green = 0
        score_red = 0
        blosum_diff_total = 0.0
        blosum_total = 0.0

        seq_rows = []

        for pos in ref_positions_sorted:
            ref_aa, ref_region = ref_map[pos]
            data_aa = data_map.get(pos, "-")

            # Default: not scored
            out_region = "DIFF0"

            # Eligible DIFF(XY) site?
            if is_scored_ref_aa(ref_aa) and ref_region.startswith("DIFF(") and ref_region.endswith(")"):
                inside = ref_region[len("DIFF(") : -1]
                if len(inside) == 2:
                    X, Y = inside[0], inside[1]  # X=good (green), Y=bad (red)

                    # Hard labeling / score
                    if data_aa == X:
                        out_region = "DIFF+"
                        score_green += 1
                    elif data_aa == Y:
                        out_region = "DIFF-"
                        score_red += 1
                    else:
                        out_region = "DIFF?"

                    # Soft scores
                    sx = sim(data_aa, X)
                    sy = sim(data_aa, Y)

                    # Discriminative
                    blosum_diff_total += (sx - sy)

                    # Preference-with-sign: choose the closer side
                    if sx > sy:
                        blosum_total += sx
                    elif sy > sx:
                        blosum_total += -sy
                    # tie -> 0

            seq_rows.append(
                {
                    "name": seq_name,
                    "position": pos,
                    "chain": ref_chain,
                    "aa": data_aa,
                    "Region": out_region,
                    "reference": name1,
                    "Score": None,
                    "BLOSUM DIFF SCORE": None,
                    "BLOSUM SCORE": None,
                }
            )

        final_score = score_green - score_red

        # Stamp totals onto each row for this sequence
        for row in seq_rows:
            row["Score"] = final_score
            row["BLOSUM DIFF SCORE"] = blosum_diff_total
            row["BLOSUM SCORE"] = blosum_total

        out_rows.extend(seq_rows)

    out_df = pd.DataFrame(out_rows)

    if outfile is not None:
        out_dir = os.path.dirname(outfile)
        if out_dir not in ("", "."):
            os.makedirs(out_dir, exist_ok=True)
        out_df.to_csv(outfile, index=False)

    return out_df