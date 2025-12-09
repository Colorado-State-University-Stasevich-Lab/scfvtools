#!/usr/bin/env python3

import sys

if len(sys.argv) < 2:
    print("Usage: python count_fasta_lengths.py <fasta_file>")
    sys.exit(1)

fasta = sys.argv[1]

name = None
seq = []

with open(fasta) as f:
    for line in f:
        line = line.strip()
        if not line:
            continue

        if line.startswith(">"):
            # If we have a previous record, print it
            if name is not None:
                full_seq = "".join(seq)
                print(f"{name}\t{len(full_seq)}")

            # Start new record
            name = line[1:]  # remove ">"
            seq = []
        else:
            seq.append(line)

# Print last record
if name is not None:
    full_seq = "".join(seq)
    print(f"{name}\t{len(full_seq)}")
