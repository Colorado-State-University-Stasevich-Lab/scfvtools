import pandas as pd

def read_excel_to_fasta(
    excel_path,
    name_column,
    sequence_column,
    output_fasta,
    contains_string=None,
    annotation_columns=None,
    list_columns=False
):
    """
    Read Excel → FASTA.
    Adds additional metadata columns into FASTA header like:
        >name|col1=VALUE|col2=VALUE

    annotation_columns: list of column names to append.
    """

    df = pd.read_excel(excel_path)

    # List columns if requested
    if list_columns:
        print("\nColumns in this Excel file:")
        for col in df.columns:
            print("  -", col)
        return None

    # Validate required columns
    if name_column not in df.columns:
        raise ValueError(f"Excel must contain name column '{name_column}'")

    if sequence_column not in df.columns:
        raise ValueError(f"Excel must contain sequence column '{sequence_column}'")

    # Validate annotation columns
    if annotation_columns:
        for col in annotation_columns:
            if col not in df.columns:
                raise ValueError(f"Requested annotation column '{col}' not found")

    # Optional substring filter (by name)
    if contains_string:
        df = df[
            df[name_column]
            .astype(str)
            .str.contains(contains_string, case=False, na=False)
        ]

    # Prepare writer
    f = open(output_fasta, "w") if output_fasta else None

    records = []

    for _, row in df.iterrows():
        raw_name = row[name_column]
        raw_seq = row[sequence_column]

        if pd.isna(raw_name) or pd.isna(raw_seq):
            continue

        name = str(raw_name).strip()
        seq = str(raw_seq).strip()

        # Skip blanks
        if name == "" or name.lower() == "nan":
            continue
        if seq == "" or seq.lower() == "nan":
            continue

        # Build extended FASTA header
        header = name

        if annotation_columns:
            for col in annotation_columns:
                val = row[col]
                # convert NaN → "NA"
                if pd.isna(val):
                    val = "NA"
                header += f"|{col}={val}"

        # Save record
        records.append((header, seq))

        if f:
            f.write(f">{header}\n{seq}\n")

    if f:
        f.close()

    return records
