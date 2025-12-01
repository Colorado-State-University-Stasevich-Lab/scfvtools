import pandas as pd
import re

# ------------------------------------------------------------
# ANSI COLOR DEFINITIONS (your colors preserved exactly)
# ------------------------------------------------------------
COLORS = {
    # Framework regions
    "FR1": "\033[95m",         # magenta
    "FR2": "\033[38;5;208m",   # bright orange
    "FR3": "\033[38;5;45m",    # cyan / aqua
    "FR4": "\033[93m",         # yellow

    # DIFF classes
    "DIFF0": "\033[90m",       # dark gray
    "DIFF+": "\033[92m",       # green   (legacy)
    "DIFF-": "\033[91m",       # red     (legacy)

    "END": "\033[0m",
}


def wrap_ansi(text, width=2000):
    return text


# ------------------------------------------------------------
# COLORIZER (DIFF(XY) aware)
# ------------------------------------------------------------
def colorize(residue, region):
    region = str(region)

    # Direct color (FR or DIFF0)
    if region in COLORS:
        return COLORS[region] + residue + COLORS["END"]

    # DIFF(XY) → green/red/dark gray
    m = re.match(r"DIFF\(([A-Z\-])([A-Z\-])\)", region)
    if m:
        X, Y = m.group(1), m.group(2)
        if residue == X:
            return COLORS["DIFF+"] + residue + COLORS["END"]
        elif residue == Y:
            return COLORS["DIFF-"] + residue + COLORS["END"]
        else:
            return COLORS["DIFF0"] + residue + COLORS["END"]

    return residue


# ------------------------------------------------------------
# SIMPLE CSV LOADER
# ------------------------------------------------------------
def show_anarci_csv(path, **kwargs):
    df = pd.read_csv(path)
    return show_anarci_df(df, **kwargs)


# ================================================================
# Build ANARCI-style 5-row numbering header (colorized)
# ================================================================
def build_numbering_header(positions, region_for_pos, colorize):
    """
    positions: list of ANARCI positions in display order (strings)
    region_for_pos: dict {pos → FR1/FR2/FR3/FR4}
    colorize: existing function to apply FR colors to characters
    """

    thousands = []
    hundreds  = []
    tens      = []
    ones      = []
    letters   = []

    for pos in positions:
        pos_str = str(pos)
        # split into digits + letter (e.g. 72A)
        num = "".join(c for c in pos_str if c.isdigit())
        let = pos_str[len(num):] if len(pos_str) > len(num) else ""

        # pad to 4 digits
        num4 = f"{int(num):04d}"

        # obtain FR region for color
        region = region_for_pos.get(pos, "FR1")

        # color each layer
        t = colorize(num4[0] if num4[0] != "0" else " ", region)
        h = colorize(num4[1] if num4[1] != "0" else " ", region)
        te = colorize(num4[2], region)
        o  = colorize(num4[3], region)
        L  = colorize(let if let else " ", region)

        thousands.append(t)
        hundreds.append(h)
        tens.append(te)
        ones.append(o)
        letters.append(L)

    header = [
        "".join(thousands),
        "".join(hundreds),
        "".join(tens),
        "".join(ones),
        "".join(letters),
    ]
    return header



# ------------------------------------------------------------
# MAIN DISPLAY FUNCTION
# ------------------------------------------------------------
def show_anarci_df(df,
                   number=True,
                   region="ALL",
                   chain="ALL",
                   legend=True,
                   annotation_filter=None):

    df = df.copy()
    df["position"] = df["position"].astype(str)

    # ------------------------------------------------------------
    # CHAIN FILTER
    # ------------------------------------------------------------
    if chain and str(chain).upper() != "ALL":
        df = df[df["chain"] == chain]

    if df.empty:
        print("❗ No rows match your chain filter.")
        return

    # ------------------------------------------------------------
    # REGION FILTER
    # ------------------------------------------------------------
    reg = region.upper()
    if reg == "FR":
        df = df[df["Region"].str.startswith("FR")]
    elif reg == "CDR":
        df = df[df["Region"].startswith("CDR")]

    if df.empty:
        print("❗ No rows match your region filter.")
        return

    # ------------------------------------------------------------
    # ANNOTATION FILTER
    # ------------------------------------------------------------
    if annotation_filter:
        for col, val in annotation_filter.items():
            df = df[df[col] == val]

        if df.empty:
            print("❗ No rows match your annotation filter.")
            return

    # ------------------------------------------------------------
    # ORDER POSITIONS
    # ------------------------------------------------------------
    def pos_sort_key(p):
        s = str(p)
        num = ''.join(c for c in s if c.isdigit())
        let = s[len(num):]
        return (int(num), let)

    positions = sorted(df["position"].unique(), key=pos_sort_key)

    # ------------------------------------------------------------
    # IDENTIFY ANNOTATION COLUMNS
    # ------------------------------------------------------------
    fixed = {"name", "position", "chain", "aa", "Region", "scheme"}
    blacklist = {"seq1", "seq2", "reference"}
    ann_cols = [c for c in df.columns if c not in fixed and c not in blacklist]

    # ------------------------------------------------------------
    # HEADER
    # ------------------------------------------------------------
    NAME_WIDTH = 28
    CHAIN_WIDTH = 4

    # ------------------------------------------------------------
    # LEGEND
    # ------------------------------------------------------------
    if legend and number:
        parts = [
            "COLOR KEY:",
            f"{colorize('F','FR1')} (FR1)",
            f"{colorize('F','FR2')} (FR2)",
            f"{colorize('F','FR3')} (FR3)",
            f"{colorize('F','FR4')} (FR4)",
            f"{colorize('X','DIFF0')} (DIFF0)",
            f"{colorize('X','DIFF(A-)')} (DIFF(XY) green/red)",
        ]
        print("  ".join(parts))
        print()

    # -------------------------------
    # Build colorized numbering header
    # -------------------------------
    if number:
        region_for_pos = {pos: regs for pos, regs in zip(positions, df["Region"])}

        header_lines = build_numbering_header(positions, region_for_pos, colorize)

        for line in header_lines:
            print(line)


    # ------------------------------------------------------------
    # PRESERVE INPUT ORDER (THE FIX!)
    # ------------------------------------------------------------
    ordered_names = df["name"].drop_duplicates().tolist()

    # ------------------------------------------------------------
    # PRINT IN ORIGINAL ORDER
    # ------------------------------------------------------------
    for name in ordered_names:
        subdf = df[df["name"] == name]
        if subdf.empty:
            continue

        chain_type = subdf["chain"].iloc[0]

        # annotation values
        ann_vals = []
        for col in ann_cols:
            vals = subdf[col].dropna().unique()
            if len(vals) == 1:
                ann_vals.append(str(vals[0]))
            else:
                ann_vals.append(",".join(str(v) for v in vals))

        # mapping
        mapping = {
            row["position"]: (row["aa"], row["Region"])
            for _, row in subdf.iterrows()
        }

        seq = []
        regs = []
        for pos in positions:
            if pos in mapping:
                aa, reg = mapping[pos]
            else:
                aa, reg = "-", "FR1"
            seq.append(aa)
            regs.append(reg)

        colored = "".join(colorize(a, r) for a, r in zip(seq, regs))

        # right side
        name_fmt = f"{name:<{NAME_WIDTH}}"
        chain_fmt = f"{chain_type:<{CHAIN_WIDTH}}"
        right = "   ".join([name_fmt, chain_fmt] + ann_vals)

        print(f"{wrap_ansi(colored)}   {right}")

    print()
