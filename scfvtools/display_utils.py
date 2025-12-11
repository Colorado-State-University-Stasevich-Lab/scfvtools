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
    "DIFF?": "\033[97m",       # bright white / unobtrusive


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

import re

# ================================================================
# Shorten names to designs (or WT) for printing convenience
# ================================================================
def shorten_name(name: str) -> str:
    """
    Human-friendly short labels for display.

    Examples:
        scFv_..._WT → WT
        design_12   → Design 12
        design12    → Design 12
        WT          → WT
        consensus_H_1_0 → H1
    """
    n = name.strip()

    # ---- WT detection ----
    # Matches:
    #   WT
    #   ..._WT
    #   ...-WT
    # but NOT "WTrange" or "myWTmutant"
    if re.search(r"(^WT$|[_\-]WT$)", n, flags=re.IGNORECASE):
        return "WT"

    # ---- Design detection ----
    m = re.search(r"design[_\-]?(\d+)", n, re.IGNORECASE)
    if m:
        return f"Design {m.group(1)}"

    # ---- Consensus detection ----
    m = re.search(r"consensus[_\-]?([HL])[_\-]?(\d+)", n, re.IGNORECASE)
    if m:
        return f"{m.group(1).upper()}{m.group(2)}"

    # fallback
    return name

# ================================================================
# HTML file start/stop writing functions
# ================================================================
def html_start(outfile, title="ANARCI Alignment"):
    """Write the HTML header once (clean, no trailing whitespace)."""
    header = f"""<!DOCTYPE html>
<html>
<head>
<meta charset="UTF-8">
<title>{title}</title>
<style>
body {{
    font-family: "JetBrains Mono", monospace;
    white-space: pre;
    font-size: 14px;
    line-height: 1.35;   /* better spacing */
}}

.seq-line {{
}}

</style>
</head>
<body>
"""
    with open(outfile, "w", encoding="utf-8") as f:
        f.write(header)

def html_end(outfile):
    """Write closing HTML tags once at the end."""
    with open(outfile, "a", encoding="utf-8") as f:
        f.write("</body>\n</html>\n")

def html_title(outfile: str, text: str):
    """Append a top-level section title (big, bold)."""
    block = f"""
<h2 style="margin-top:24px; margin-bottom:8px; font-size:20px; font-weight:bold;">
    {text}
</h2>
"""
    with open(outfile, "a", encoding="utf-8") as f:
        f.write(block)


def html_subtitle(outfile: str, text: str):
    """Append a subsection header (slightly smaller)."""
    block = f"""
<h3 style="margin-top:16px; margin-bottom:6px; font-size:16px; font-weight:bold;">
    {text}
</h3>
"""
    with open(outfile, "a", encoding="utf-8") as f:
        f.write(block)


def html_paragraph(outfile: str, text: str):
    """Append a paragraph of normal text."""
    block = f"""
<p style="margin-top:6px; margin-bottom:6px; font-size:14px; line-height:1.35;">
    {text}
</p>
"""
    with open(outfile, "a", encoding="utf-8") as f:
        f.write(block)


def html_hr(outfile: str):
    """Append a horizontal divider line."""
    block = """
<hr style="border:0; border-top:1px solid #ddd; margin-top:16px; margin-bottom:16px;">
"""
    with open(outfile, "a", encoding="utf-8") as f:
        f.write(block)


# ------------------------------------------------------------
# MAIN DISPLAY FUNCTION
# ------------------------------------------------------------
def show_anarci_df(df,
                   number=True,
                   region="ALL",
                   chain="ALL",
                   legend=True,
                   annotation_filter=None,
                   show_header=True):

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
    NAME_WIDTH =  10
    CHAIN_WIDTH = 4

    # ------------------------------------------------------------
    # LEGEND
    # ------------------------------------------------------------
    if legend and number:
        parts = [
            "COLOR KEY:",
            f"{colorize('FR1','FR1')}",
            f"{colorize('FR2','FR2')}",
            f"{colorize('FR3','FR3')}",
            f"{colorize('FR4','FR4')}",
            f"{colorize('DIFF0','DIFF0')}",
            f"{colorize('DIFF+','DIFF+')}",
            f"{colorize('DIFF-','DIFF-')}",
            f"{colorize('DIFF?','DIFF?')}",   
        ]
        print("  ".join(parts))

    # ------------------------------------------------------------
    # PRESERVE INPUT ORDER (THE FIX!)
    # ------------------------------------------------------------
    ordered_names = df["name"].drop_duplicates().tolist()

    # ------------------------------------------------------------
    # PRINT COLUMN HEADER (aligned above sequences) — OPTIONAL
    # ------------------------------------------------------------
    if show_header:
        seq_width = len(positions)          # width of colored sequence block
        header_seq = " " * seq_width        # blank space to align header above sequence

        # Header labels
        header_right = f"{'Name':<{NAME_WIDTH}}   {'Chain':<{CHAIN_WIDTH}}"

        for col in ann_cols:
            header_right += f"   {col.upper()}"

        print(header_seq + "   " + header_right)
        print("-" * (seq_width + len(header_right) + 3))

    # -------------------------------
    # Build colorized numbering header
    # -------------------------------
    if number:
        region_for_pos = {pos: regs for pos, regs in zip(positions, df["Region"])}

        header_lines = build_numbering_header(positions, region_for_pos, colorize)

        for line in header_lines:
            print(line)

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
        short = shorten_name(name)
        name_fmt = f"{short:<{NAME_WIDTH}}"

        chain_fmt = f"{chain_type:<{CHAIN_WIDTH}}"
        right = "   ".join([name_fmt, chain_fmt] + ann_vals)

        print(f"{wrap_ansi(colored)}   {right}")


# =============================================================
# Export ANARCI-style alignment as true HTML (NOT ANSI-converted)
# =============================================================
def show_anarci_html(path,
                     outfile,
                     number=True,
                     region="ALL",
                     chain="ALL",
                     legend=True,
                     annotation_filter=None,
                     show_header=True):
    """
    Produces EXACTLY the same alignment as show_anarci_df(),
    but renders HTML instead of ANSI escape codes.
    """

    df = pd.read_csv(path).copy()
    df["position"] = df["position"].astype(str)

    # ------------------------------------------------------------
    # Apply filters (same logic as show_anarci_df)
    # ------------------------------------------------------------
    if chain and str(chain).upper() != "ALL":
        df = df[df["chain"] == chain]

    reg = region.upper()
    if reg == "FR":
        df = df[df["Region"].str.startswith("FR")]
    elif reg == "CDR":
        df = df[df["Region"].str.startswith("CDR")]

    if annotation_filter:
        for col, val in annotation_filter.items():
            df = df[df[col] == val]

    if df.empty:
        raise ValueError("No rows match the selected filters.")

    # ------------------------------------------------------------
    # Sort positions
    # ------------------------------------------------------------
    def pos_sort_key(p):
        s = str(p)
        num = ''.join(c for c in s if c.isdigit())
        let = s[len(num):]
        return (int(num), let)

    positions = sorted(df["position"].unique(), key=pos_sort_key)

    # ------------------------------------------------------------
    # HTML colorizer (replacing ANSI colorize)
    # ------------------------------------------------------------
    REGION_COLOR = {
        # Framework FR1-FR4 unchanged (assuming you keep previous muted palette)
        "FR1": "#4F81BD",
        "FR2": "#B8860B",
        "FR3": "#5F9EA0",
        "FR4": "#6A5ACD",

        # Updated DIFF classes (white-background optimized)
        "DIFF0": "#DDDDDD",   # light gray (very unobtrusive)
        "DIFF+": "#006400",   # dark green 
        "DIFF-": "#B22222",   # red 
        "DIFF?": "#AAAAAA",   # gray for HTML

    }


    def color_html(residue, region):
        """Return HTML-colored residue with proper DIFF logic."""
        
        region = str(region).strip().upper()   # ← removes spaces and normalizes case

        # FR regions
        if region in REGION_COLOR:
            return f"<span class='seq-res' style='color:{REGION_COLOR[region]}'>{residue}</span>"

        # DIFF(XY)
        m = re.match(r"DIFF\(([A-Z\-])([A-Z\-])\)", region)
        if m:
            X, Y = m.group(1), m.group(2)
            if residue == X:
                return f"<span class='seq-res' style='color:{REGION_COLOR['DIFF+']}'><b>{residue}</b></span>"
            elif residue == Y:
                return f"<span class='seq-res' style='color:{REGION_COLOR['DIFF-']}'><b>{residue}</b></span>"
            else:
                return f"<span class='seq-res' style='color:{REGION_COLOR['DIFF0']}'>{residue}</span>"

        # CLASSIFIED DIFF
        if region == "DIFF+":
            return f"<span class='seq-res' style='color:{REGION_COLOR['DIFF+']}'><b>{residue}</b></span>"

        if region == "DIFF-":
            return f"<span class='seq-res' style='color:{REGION_COLOR['DIFF-']}'><b>{residue}</b></span>"

        if region == "DIFF?":
            return f"<span class='seq-res' style='color:{REGION_COLOR['DIFF?']}'>{residue}</span>"

        if region == "DIFF0":
            return f"<span class='seq-res' style='color:{REGION_COLOR['DIFF0']}'>{residue}</span>"

        return residue




    # ------------------------------------------------------------
    # Build numbering header (HTML version)
    # ------------------------------------------------------------
    region_for_pos = {pos: regs for pos, regs in zip(positions, df["Region"])}

    header_lines = build_numbering_header(positions, region_for_pos, color_html)

    # ------------------------------------------------------------
    # Build HTML body
    # ------------------------------------------------------------
    html_lines = []

    # legend
    if legend and number:
        html_lines.append("<b>COLOR KEY:</b> ")

        # color the region labels instead of an example residue
        html_lines.append(f"<span style='color:{REGION_COLOR['FR1']}'><b>FR1</b></span>&nbsp; ")
        html_lines.append(f"<span style='color:{REGION_COLOR['FR2']}'><b>FR2</b></span>&nbsp; ")
        html_lines.append(f"<span style='color:{REGION_COLOR['FR3']}'><b>FR3</b></span>&nbsp; ")
        html_lines.append(f"<span style='color:{REGION_COLOR['FR4']}'><b>FR4</b></span>&nbsp; ")

        # DIFF scores
        html_lines.append(f"<span style='color:{REGION_COLOR['DIFF0']}'><b>DIFF0</b></span>&nbsp; ")
        html_lines.append(f"<span style='color:{REGION_COLOR['DIFF+']}; font-weight:bold'>DIFF+</span>&nbsp; ")
        html_lines.append(f"<span style='color:{REGION_COLOR['DIFF-']}; font-weight:bold'>DIFF-</span>&nbsp; ")
        html_lines.append(f"<span style='color:{REGION_COLOR['DIFF?']}; font-weight:bold'>DIFF?</span>&nbsp; ")


        html_lines.append("<br><br>")

    # sequences
    ordered_names = df["name"].drop_duplicates().tolist()
    # Identify annotation (score) columns same way as show_anarci_df
    fixed = {"name", "position", "chain", "aa", "Region", "scheme"}
    blacklist = {"seq1", "seq2", "reference"}
    ann_cols = [c for c in df.columns if c not in fixed and c not in blacklist]


    NAME_WIDTH =  10
    CHAIN_WIDTH = 4
    # ------------------------------------------------------------
    # HTML HEADER ROW (OPTIONAL)
    # ------------------------------------------------------------
    if show_header:
        seq_width = len(positions)
        blank_seq = "&nbsp;" * seq_width

        header = f"<span>{blank_seq}</span>&nbsp;&nbsp;&nbsp;"

        # Labels (cleaner, matching df print-out)
        header += f"<b>{'Name':<{NAME_WIDTH}}</b>&nbsp;&nbsp;"
        header += f"<b>{'Chain':<{CHAIN_WIDTH}}</b>&nbsp;&nbsp;"

        for col in ann_cols:
            header += f"<b>{col.upper()}</b>&nbsp;&nbsp;"

        html_lines.append(header + "<br>")

    # numbering header
    if number:
        for line in header_lines:
            html_lines.append(line + "<br>")

    for name in ordered_names:
        subdf = df[df["name"] == name]
        chain_type = subdf["chain"].iloc[0]

        # annotation columns: same logic as show_anarci_df
        ann_vals = []
        for col in ann_cols:
            vals = subdf[col].dropna().unique()
            if len(vals) == 1:
                ann_vals.append(str(vals[0]))
            else:
                ann_vals.append(",".join(str(v) for v in vals))

        mapping = {
            row["position"]: (row["aa"], row["Region"])
            for _, row in subdf.iterrows()
        }

        seq_html = []
        for pos in positions:
            if pos in mapping:
                aa, reg = mapping[pos]
            else:
                aa, reg = "-", "FR1"
            seq_html.append(color_html(aa, reg))

        sequence_part = "".join(seq_html)

        # Right side with annotation values including "score"
        short = shorten_name(name)
        # collect annotation values
        ann_vals = []
        for col in ann_cols:
            vals = subdf[col].dropna().unique()
            if len(vals) == 1:
                ann_vals.append(str(vals[0]))
            else:
                ann_vals.append(",".join(str(v) for v in vals))

        ann_str = " &nbsp;&nbsp; ".join(ann_vals)

        right = f"{short:<{NAME_WIDTH}} &nbsp;&nbsp; {chain_type:<{CHAIN_WIDTH}} &nbsp;&nbsp; {ann_str}"

        html_lines.append(sequence_part + "&nbsp;&nbsp;&nbsp;" + right + "<br>")

    # ALWAYS append — the wrapper is now handled outside
    final_block = "".join(html_lines)

    with open(outfile, "a", encoding="utf-8") as f:
        f.write(final_block)

    print(f"✔ HTML alignment appended to: {outfile}")

