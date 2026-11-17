"""Fixtures for the end-to-end pipeline baseline test.

The pipeline steps resolve config and output folders from a module-level
`projectPath` (the repo root). To keep the real repo untouched, the test builds
a throw-away project in tmp_path and points every step module at it.
"""
import os
import sys
import shutil
import pathlib
import importlib

import pytest
import yaml

HERE = pathlib.Path(__file__).resolve().parent
ROOT = HERE.parents[1]
for p in (ROOT, ROOT / "dima", ROOT / "tests"):   # notebook imports + shared test helpers
    if str(p) not in sys.path:
        sys.path.insert(0, str(p))
FIXTURES = HERE / "fixtures"

# Real-data mode: point these at your data instead of the (future) fixture.
#   ACSM_TEST_DESCRIPTOR  campaignDescriptor.yaml whose input_file_directory is the real data
#   ACSM_BASELINE_DIR     where the baseline lives (outside the repo; real outputs are large)
DESCRIPTOR = pathlib.Path(os.environ.get("ACSM_TEST_DESCRIPTOR", FIXTURES / "campaignDescriptor.yaml"))
BASELINE = pathlib.Path(os.environ.get("ACSM_BASELINE_DIR", HERE / "baseline"))

STEP_MODULES = [
    "pipelines.steps.update_datachain_params",
    "pipelines.steps.apply_calibration_factors",
    "pipelines.steps.generate_flags",
    "pipelines.steps.prepare_ebas_submission",
    "pipelines.steps.update_actris_header",
    "pipelines.steps.drop_column_from_nas_file",
    "pipelines.steps.adjust_uncertainty_column_in_nas_file",
]


def pytest_addoption(parser):
    parser.addoption("--update-baseline", action="store_true",
                     help="Overwrite tests/pipeline/baseline with the current outputs.")


@pytest.fixture
def update_baseline(request):
    return request.config.getoption("--update-baseline")


@pytest.fixture
def project(tmp_path, monkeypatch):
    """A disposable copy of the parts of the repo the steps read or write."""
    if not os.environ.get("LEGACY_PYTHON"):
        pytest.skip("Set LEGACY_PYTHON to the legacy converter interpreter.")
    if not DESCRIPTOR.exists():
        pytest.skip(f"Descriptor not found: {DESCRIPTOR}")
    descriptor = yaml.safe_load(DESCRIPTOR.read_text())
    if "ACSM_TEST_DESCRIPTOR" not in os.environ:                 # fixture mode
        descriptor["input_file_directory"] = str(FIXTURES / "raw") + "/"
    if not os.path.isdir(os.path.expandvars(descriptor["input_file_directory"])):
        pytest.skip(f"Input data not found: {descriptor['input_file_directory']}")

    proj = tmp_path / "project"
    # Config the steps read (and that update_datachain_params overwrites).
    shutil.copytree(ROOT / "pipelines", proj / "pipelines")
    shutil.copytree(ROOT / "app" / "flags", proj / "app" / "flags")
    # Converter code + header cfg (update_actris_header writes into it).
    shutil.copytree(ROOT / "third_party" / "acsmProcessingSoftware" / "src",
                    proj / "third_party" / "acsmProcessingSoftware" / "src")
    (proj / "data").mkdir()

    # Outputs always go to the temp project; real data is only read.
    descriptor["output_file_directory"] = str(proj / "data") + "/"
    descriptor.setdefault("test_month_range", "2-3")
    (proj / "campaignDescriptor.yaml").write_text(yaml.safe_dump(descriptor, sort_keys=False))

    # Point every step at the temp project instead of the real repo.
    for name in STEP_MODULES:
        monkeypatch.setattr(importlib.import_module(name), "projectPath", str(proj))

    monkeypatch.chdir(proj)
    return proj
