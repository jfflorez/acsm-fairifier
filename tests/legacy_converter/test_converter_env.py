# NOTE: the converter identifies input files by name (e.g. JFJ_ACSM-017_2024.txt),
# so the cropped fixtures must keep the original file names.
import hashlib
import pathlib

import pytest

from pipelines.steps.utils import run_script  # adjust to wherever you put it

HERE = pathlib.Path(__file__).parent
ROOT = HERE.parents[1]
SCRIPT = ROOT / "third_party/acsmProcessingSoftware/src/rawto012.py"
INFILE = HERE / "data/JFJ_ACSM-017_2024.txt"
FLAGS = HERE / "data/JFJ_ACSM-017_FLAGS_2024.txt"
BASELINE = HERE / "baseline"


def content_hashes(folder):
    """Hash file contents with each file's own creation stamp masked.

    The stamp (3rd dot-separated field of the file name) is also written
    inside the file and changes on every run. Hidden files are ignored.
    """
    folder = pathlib.Path(folder)
    hashes = []
    for p in folder.rglob("*"):
        if p.is_file() and not any(part.startswith(".") for part in p.relative_to(folder).parts):
            stamp = p.name.split(".")[2].encode()
            hashes.append(hashlib.md5(p.read_bytes().replace(stamp, b"<CREATED>")).hexdigest())
    return sorted(hashes)

@pytest.mark.parametrize("python", [
    "/opt/conda/envs/apog_penv/bin/python",   # determinism check; drop after decoupling
    "/opt/conda/envs/acsm_legacy/bin/python",
])
def test_output_matches_baseline(python, tmp_path):
    print(f"\n[interpreter] {python}")
    print(f"[input]       {INFILE}")
    print(f"[flags]       {FLAGS}")
    print(f"[baseline]    {BASELINE}")
    print(f"[output dir]  {tmp_path}")

    assert INFILE.exists() and FLAGS.exists(), f"missing fixtures: {INFILE}, {FLAGS}"
    assert BASELINE.exists(), f"missing baseline: {BASELINE}"
    print("[check] fixtures and baseline exist")

    run_script(python, SCRIPT, [INFILE, FLAGS, f"{tmp_path}/"], cwd=ROOT)
    print("[check] converter ran without error")

    fresh = content_hashes(tmp_path)
    expected = content_hashes(BASELINE)
    print(f"[check] files produced: {len(fresh)}, files in baseline: {len(expected)}")
    assert len(fresh) == len(expected), "different number of output files"

    print("[check] content compared with creation stamp masked and hidden files ignored")
    assert fresh == expected
    print("[result] outputs identical to baseline")