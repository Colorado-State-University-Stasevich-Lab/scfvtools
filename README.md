# scfvtools

Utilities for comparing scFv (or antibody) sequences to reference
consensus sequences and generating per-position consensus scoring tables
from FASTA or Excel inputs.

------------------------------------------------------------------------

## Installation

This repository uses a Conda environment (`environment.yml`) plus a
standard Python package install (`setup.py`).

### 1. Clone the repository

``` bash
git clone git@github.com:Colorado-State-University-Stasevich-Lab/scfvtools.git
cd scfvtools
```

(HTTPS cloning also works if you prefer tokens.)

------------------------------------------------------------------------

### 2. Create the Conda environment

This example assumes Miniforge is installed at:

    /home/<username>/miniforge3

Create the environment at a specific prefix:

``` bash
conda env create   --prefix /home/<username>/miniforge3/envs/scfvtools_env   -f environment.yml
```

If the environment already exists and needs updating:

``` bash
conda env update   --prefix /home/<username>/miniforge3/envs/scfvtools_env   -f environment.yml   --prune
```

------------------------------------------------------------------------

### 3. Activate the environment

Because a prefix was used, activate via full path:

``` bash
conda activate /home/<username>/miniforge3/envs/scfvtools_env
```

Confirm:

``` bash
which python
```

It should point to the environment you just created.

------------------------------------------------------------------------

### 4. Install the package (editable mode)

From the repository root:

``` bash
python -m pip install -e .
```

Editable mode (`-e`) ensures that local code changes are immediately
reflected without reinstalling.

------------------------------------------------------------------------

## Running the Example Test Script

An example test script is provided in:

    scripts/test_fasta_compare_to_consensus.sh

### Important: Ensure output directory exists

The script writes to `output_dir/`. Create it once:

``` bash
mkdir -p output_dir
```

------------------------------------------------------------------------

### Run the test

From inside the `scripts/` directory:

``` bash
cd scripts
bash test_fasta_compare_to_consensus.sh
```

You should see:

    === FASTA ===
    [INFO] Running make_score_df ...
    ...
    === EXCEL ===
    ...

Output CSV files will be written to:

    output_dir/

------------------------------------------------------------------------

## Direct CLI Usage

The core script can be run directly:

``` bash
python scripts/fasta_compare_to_consensus.py   --ref_csv example_data/diff_H.csv   --name H   --data_fasta example_data/WNV_5D4.fasta   --out output_dir/WNV_5D4_consensus_scores.csv
```

Or using Excel input:

``` bash
python scripts/fasta_compare_to_consensus.py   --ref_csv example_data/diff_H.csv   --name H   --excel example_data/test_scFvs.xlsx   --name_column name   --seq_column sequence   --out output_dir/test_scFvs_consensus_scores.csv
```

------------------------------------------------------------------------

## Notes

-   Designed for Linux / macOS environments.
-   Recommended to use Miniforge (conda-forge channel priority).
-   If using ARM (linux-aarch64), avoid exporting fully pinned
    environments from x86 systems.
-   If adding new dependencies, update `environment.yml` and reinstall
    via:

``` bash
conda env update --prefix /home/<username>/miniforge3/envs/scfvtools_env -f environment.yml --prune
```

------------------------------------------------------------------------

## Development Workflow

After activation:

``` bash
conda activate /home/<username>/miniforge3/envs/scfvtools_env
cd scfvtools
python -m pip install -e .
```

Then modify code as needed. No reinstall required.
