## Testing

How the pipeline test works, step by step: [tests/pipeline/docs/test_flow.svg](/tests/pipeline/docs/test_flow.svg).
What the sample data contains and why: [tests/pipeline/pipeline/docs/README.md](/tests/pipeline/docs/README.md).

### Run the tests

Inside the container (the dima submodule must be checked out:
`git submodule update --init`):

```bash
docker compose exec datachain_processor bash      # Git Bash on Windows: prefix with winpty
cd /workspace/acsm-fairifier
conda activate apog_penv
pip install pytest                                # not in environment.yml yet

pytest tests/legacy_converter -s                  # converter only
pytest tests/pipeline -s                          # whole pipeline on the sample data
```

A pass means the outputs are identical to the baseline (CSVs within a
relative tolerance of 1e-9; dates that change on every run are masked). A
failure names the file that differs.

### After an intended change in the outputs

Check the new outputs, then accept them as the new baseline and commit the
baseline together with the change:

```bash
pytest tests/pipeline -s --update-baseline
git add tests/pipeline/baseline
```

### Run on a full year of real data

Point the test at a descriptor whose `input_file_directory` is the real input,
and keep that (large) baseline outside the repository:

```bash
cp campaignDescriptor.yaml /tmp/test_descriptor.yaml   # edit input_file_directory in the copy
export ACSM_TEST_DESCRIPTOR=/tmp/test_descriptor.yaml
export ACSM_BASELINE_DIR=/path/outside/repo/acsm_baseline
pytest tests/pipeline -s --update-baseline             # once, on code you trust
pytest tests/pipeline -s                               # after each change
```

### Rebuild the sample data

```bash
bash tests/pipeline/make_fixture.sh <input_dir> <start YYYY-MM-DD> <end YYYY-MM-DD> --force
```

Then regenerate the baseline with `--update-baseline`. Which files are cut,
copied or left out is described in
[tests/pipeline/docs/README.md](tests/pipeline/docs/README.md).

### Keep the repository clean when running notebooks

The tests never change the repository, but running the pipeline notebooks
rewrites `pipelines/params/` and the ACTRIS header files. On the host, open
the container shell with:

```bash
bash scripts/docker_shell.sh
```

When you leave the shell, those files are restored to their state before the
session (your own uncommitted edits are kept).