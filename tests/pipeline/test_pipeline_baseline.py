"""End-to-end baseline (characterization) test of notebooks/demo_acsm_pipeline.ipynb.

Runs the notebook's steps in the same order and keeps a copy of what the run
leaves in the project's data/ and pipelines/params/ folders, with the same
folder structure (dima's raw copy included, the .h5 left out). Only names that
change on every run are mapped:
  * dima's output folder collection_..._<today>  -> collection
  * the .nas creation stamp in file names        -> CREATED
Inside files, the temp project path becomes <PROJECT>, dima's folder name
becomes collection, and each .nas file's own stamp/date becomes <CREATED>/<DATE>.
Paths of calibrated and flags CSVs come from the steps' return values.

Real data:
    export LEGACY_PYTHON=/opt/conda/envs/acsm_legacy/bin/python
    export ACSM_TEST_DESCRIPTOR=/path/to/campaignDescriptor.yaml   # input_file_directory = real data
    export ACSM_BASELINE_DIR=/path/outside/repo/acsm_baseline_JFJ_2024
    pytest tests/pipeline -s --update-baseline   # once, on the current code
    pytest tests/pipeline -s                     # after every fix

Fixture mode: unset ACSM_TEST_DESCRIPTOR / ACSM_BASELINE_DIR and fill
tests/pipeline/fixtures/raw; the baseline then lives in tests/pipeline/baseline.
"""
import json
import shutil
import pathlib

import pandas as pd
import pytest
import yaml

from conftest import BASELINE
from nas_masking import mask_name, mask_content     # shared with tests/legacy_converter

from dima.pipelines.data_integration import run_pipeline as get_campaign_data
from pipelines.steps.update_datachain_params import main as update_datachain_params
from pipelines.steps.apply_calibration_factors import main as apply_calibration_factors
from pipelines.steps.generate_flags import main as generate_flags
from pipelines.steps.update_actris_header import main as update_actris_header
from pipelines.steps.prepare_ebas_submission import main as prepare_ebas_submission
from pipelines.steps.drop_column_from_nas_file import main as drop_column_from_nas_file
from pipelines.steps.adjust_uncertainty_column_in_nas_file import main as adjust_uncertainty

SPECIES = ["Org", "NO3", "NH4", "SO4", "Chl"]


def ok(result):
    """Steps signal failure inconsistently (None, 1, dict); fail loudly here."""
    assert isinstance(result, dict) and result.get("status") == "success", result
    return result


def output_paths(result, proj):
    """Paths a step reports in result['outputs'] (relative to the project root)."""
    return [proj / spec["path"] for _, spec in result["outputs"]]


# ---------------------------------------------------------------- run pipeline
def run_pipeline(proj: pathlib.Path):
    desc = yaml.safe_load((proj / "campaignDescriptor.yaml").read_text())
    month = desc["test_month_range"]
    inst_folder = desc["instrument_datafolder"][0]

    h5_file = get_campaign_data(str(proj / "campaignDescriptor.yaml"))[0]

    ok(update_datachain_params(h5_file, inst_folder))
    calib = ok(apply_calibration_factors(h5_file, str(proj / "pipelines/params/calibration_factors.yaml")))
    ok(generate_flags(h5_file, "diagnostics"))
    ok(generate_flags(h5_file, "cpc"))
    species = ok(generate_flags(h5_file, "species"))        # reads the two above

    processed = [str(p) for p in output_paths(calib, proj)]  # calibrated, err, factors
    flags = str(output_paths(species, proj)[0])

    update_actris_header(str(proj / "campaignDescriptor.yaml"))
    ok(prepare_ebas_submission(processed, flags, month))

    # The converter's .nas outputs are not in prepare_ebas_submission's return value.
    lev2 = sorted((proj / "data").rglob("*.lev2.nas"))
    assert len(lev2) == 1, f"expected one lev2 .nas file, got {lev2}"
    drop_column_from_nas_file(str(lev2[0]), column_to_remove="inletP")
    adjust_uncertainty(str(lev2[0]), base_column_names=SPECIES)

    # Mirror the project's output folders as they are. Only run-dependent names change:
    # dima's output folder (name contains today's date) -> "collection", and each
    # .nas creation stamp -> CREATED. The .h5 is binary and left out.
    collection = pathlib.Path(h5_file).stem
    replacements = {str(proj): "<PROJECT>", collection: "collection"}
    out = proj / "_results"
    for top in ("data", "pipelines/params"):
        for p in sorted((proj / top).rglob("*")):
            if not p.is_file() or p.suffix == ".h5":
                continue
            rel = pathlib.Path(*[("collection" if part == collection else part)
                                 for part in p.relative_to(proj).parts])
            write_masked(p, out / rel.with_name(normalize_name(rel.name)), replacements)
    return out


# ------------------------------------------------------------------ masking
def normalize_name(name: str) -> str:
    return mask_name(name) if name.endswith(".nas") else name


def write_masked(src: pathlib.Path, dest: pathlib.Path, replacements: dict):
    """Copy src to dest with run-specific strings replaced."""
    data = src.read_bytes()
    for old, new in replacements.items():
        data = data.replace(old.encode(), new.encode())
    if src.suffix == ".nas":
        data = mask_content(src.name, data)
    dest.parent.mkdir(parents=True, exist_ok=True)
    dest.write_bytes(data)


def compare_file(new: pathlib.Path, ref: pathlib.Path):
    if new.suffix == ".csv":
        pd.testing.assert_frame_equal(pd.read_csv(new), pd.read_csv(ref),
                                      check_exact=False, rtol=1e-9, obj=new.name)
    elif new.suffix == ".json":                                     # lineage metadata
        load = lambda p: {k: {kk: vv for kk, vv in v.items() if kk != "processing_date"}
                          for k, v in json.loads(p.read_text()).items()}
        assert load(new) == load(ref), new.name
    else:                                                           # .nas, .txt, .yaml
        assert new.read_text() == ref.read_text(), new.name


# ---------------------------------------------------------------------- test
def test_pipeline_matches_baseline(project, update_baseline):
    results = run_pipeline(project)

    if update_baseline:
        # Only replace a folder this test created (marker file), never an arbitrary one.
        if BASELINE.exists() and any(BASELINE.iterdir()) and not (BASELINE / ".acsm_baseline").exists():
            pytest.fail(f"{BASELINE} is not empty and not a baseline folder; refusing to overwrite.")
        shutil.rmtree(BASELINE, ignore_errors=True)
        shutil.copytree(results, BASELINE)
        (BASELINE / ".acsm_baseline").touch()
        pytest.skip(f"Baseline written to {BASELINE}; review it before relying on it.")

    if not BASELINE.exists():
        pytest.fail(f"No baseline at {BASELINE}. Run once with --update-baseline.")
    new = {p.relative_to(results) for p in results.rglob("*") if p.is_file()}
    ref = {p.relative_to(BASELINE) for p in BASELINE.rglob("*")
           if p.is_file() and p.name != ".acsm_baseline"}
    assert new == ref, f"missing: {sorted(ref - new)}\nunexpected: {sorted(new - ref)}"

    for rel in sorted(new):
        compare_file(results / rel, BASELINE / rel)
