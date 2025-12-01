import os
import pytest
from scfvtools.anarci_utils import run_anarci_and_align_fasta


def test_anarci_align_single_vh(tmp_path):
    """
    Test ANARCI on a full VH sequence.
    Should detect CHAIN=H and produce aligned output with gaps.
    """

    seq = (
        "EVQLVESGGGLVQPGGSLRLSCAASGFTFSSYAMSWVRQAPGKGLEWVSAISSSGGGSTYYADSVKGRFT"
        "ISRDNNAKNSLYLQMNSLRAEDTAVYYCARRDYWGQGTSVTVSS"
    )

    fasta = tmp_path / "input.fasta"
    output = tmp_path / "aligned.fasta"

    fasta.write_text(f">VH_test\n{seq}\n")

    run_anarci_and_align_fasta(str(fasta), str(output), scheme="martin")

    assert output.exists(), "Aligned FASTA file should be created"
    contents = output.read_text()

    assert "CHAIN=H" in contents, "Should annotate heavy chain"
    assert "GERM=IGHV" in contents, "Should annotate fixed IGHV germline label"
    assert "-" in contents, "Aligned sequence should contain gaps"
    assert len(contents.splitlines()) >= 2


def test_anarci_align_scfv_multichain(tmp_path):
    """
    Test scFv containing both VH and VL.
    """

    vh = (
        "EVQLVESGGGLVQPGGSLRLSCAASGFTFSSYAMSWVRQAPGKGLEWVSAISSSGGGSTYYADSVKGRFT"
        "ISRDNNAKNSLYLQMNSLRAEDTAVYYCARRDYWGQGTSVTVSS"
    )
    linker = "GGGGSGGGGSGGGGS"
    vl = (
        "DIQMTQSPASLSASVGDRVTITCKASQDVSTAVAWYQQKPGKAPKLLIYDTSTLAESDVPSRFSGSGSGTD"
        "FTLTISRLEPEDFAVYYCQHYTTPPTFGQGTKVEIK"
    )

    scfv = vh + linker + vl

    fasta = tmp_path / "scfv.fasta"
    output = tmp_path / "scfv_aligned.fasta"

    fasta.write_text(f">scfv_test\n{scfv}\n")

    run_anarci_and_align_fasta(str(fasta), str(output), scheme="martin")
    contents = output.read_text()

    assert "CHAIN=H" in contents, "VH chain should be detected"
    assert ("CHAIN=L" in contents or "CHAIN=K" in contents), "VL chain should be detected"

    # fixed germline labels
    assert "GERM=IGHV" in contents, "Heavy chain germline label present"
    assert ("GERM=IGLV" in contents or "GERM=IGKV" in contents), "Light chain germline label present"

    assert contents.count(">") >= 2, "Should generate VH and VL entries"


def test_empty_fasta_raises_error(tmp_path):
    empty = tmp_path / "empty.fasta"
    empty.write_text("")

    output = tmp_path / "out.fasta"

    with pytest.raises(ValueError):
        run_anarci_and_align_fasta(str(empty), str(output))
