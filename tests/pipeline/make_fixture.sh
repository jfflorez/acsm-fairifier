#!/usr/bin/env bash
# Build the small test input in tests/pipeline/fixtures/ from a real input folder.
#
# Usage (inside the container, from the repo root, in the apog_penv env):
#   bash tests/pipeline/make_fixture.sh <input_dir> <start> <end> [--force]
#
#   <input_dir>  the folder you would put in input_file_directory
#                e.g. Data/collection_1_JFJ_2024_2025-09-23
#   <start>      first day kept, YYYY-MM-DD (inclusive)
#   <end>        day after the last day kept, YYYY-MM-DD (exclusive)
#
# Example: keep 2024-02-27 .. 2024-03-01
#   bash tests/pipeline/make_fixture.sh Data/collection_1_JFJ_2024_2025-09-23 2024-02-27 2024-03-02
#
# Rules (anything else stops the script and lists the file, nothing is guessed)
#   params/**            copied unchanged
#   *.txt                header kept, rows whose first timestamp is in the window kept
#                        (dd.mm.yyyy HH:MM:SS, yyyy-mm-dd HH:MM:SS, yyyy/mm/dd HH:MM:SS)
#   *.nas (NASA Ames)    header block kept, rows whose time (days since the file's
#                        reference date) is in the window kept
#   Org_*.csv            left out of the fixture (see tests/pipeline/fixtures/README.md)
# Lines are kept or dropped byte for byte; values are never rewritten.
# At the end it checks the pipeline will find exactly one *_timeseries.txt, one
# *_meta.txt and one CPC .nas file, and writes fixtures/campaignDescriptor.yaml
# with test_month_range set from the window.
set -euo pipefail

if [[ $# -lt 3 ]]; then
  sed -n '2,25p' "$0"; exit 1
fi

REPO="$(cd "$(dirname "$0")/../.." && pwd)"
SRC="$1"; START="$2"; END="$3"; FORCE="${4:-}"
DEST="$REPO/tests/pipeline/fixtures/raw"

if [[ -d "$DEST" && -n "$(ls -A "$DEST" 2>/dev/null)" ]]; then
  if [[ "$FORCE" != "--force" ]]; then
    echo "$DEST is not empty. Re-run with --force to replace it."; exit 1
  fi
  rm -rf "$DEST"
fi
mkdir -p "$DEST"

python - "$REPO" "$SRC" "$DEST" "$START" "$END" <<'PY'
import re, sys, shutil, pathlib
from datetime import datetime, timedelta
import yaml

repo, src, dest, start, end = sys.argv[1:]
repo, src, dest = pathlib.Path(repo), pathlib.Path(src).resolve(), pathlib.Path(dest)
t0, t1 = datetime.fromisoformat(start), datetime.fromisoformat(end)
assert t0 < t1, "start must be before end"

desc = yaml.safe_load((repo / "campaignDescriptor.yaml").read_text())
inst_folders = desc["instrument_datafolder"]

PATTERNS = [  # (regex on bytes, order of day/month/year groups)
    (re.compile(rb"(\d{2})\.(\d{2})\.(\d{4})[ T](\d{2}):(\d{2}):(\d{2})"), "dmY"),
    (re.compile(rb"(\d{4})-(\d{2})-(\d{2})[ T](\d{2}):(\d{2}):(\d{2})"), "Ymd"),
    (re.compile(rb"(\d{4})/(\d{2})/(\d{2})[ T](\d{2}):(\d{2}):(\d{2})"), "Ymd"),
]

def first_timestamp(line: bytes):
    best = None
    for rx, order in PATTERNS:
        m = rx.search(line)
        if m and (best is None or m.start() < best[0]):
            g = [int(x) for x in m.groups()]
            d, mo, y = (g[0], g[1], g[2]) if order == "dmY" else (g[2], g[1], g[0])
            try:
                best = (m.start(), datetime(y, mo, d, g[3], g[4], g[5]))
            except ValueError:
                pass
    return best[1] if best else None

def slice_text(lines):
    stamps = [first_timestamp(l) for l in lines]
    # data starts at the first of two consecutive timestamped lines
    # (a single date in the header, e.g. "created ...", is not data)
    start_idx = next((i for i in range(len(lines) - 1) if stamps[i] and stamps[i + 1]), None)
    if start_idx is None:
        return None, "no timestamped rows recognised"
    keep = lines[:start_idx]
    rows = dropped_undated = 0
    for line, ts in zip(lines[start_idx:], stamps[start_idx:]):
        if ts is None:
            dropped_undated += 1
        elif t0 <= ts < t1:
            keep.append(line); rows += 1
    note = f"{rows}/{len(lines) - start_idx} rows kept"
    if dropped_undated:
        note += f", {dropped_undated} undated lines after header dropped"
    return (keep if rows else None), note

def slice_nasa_ames(lines):
    nlhead = int(lines[0].split()[0])                          # header incl. column-name line
    # Origin as in dima's read_nasa_ames_as_dict: the "Startdate:" header entry
    start = [l for l in lines[:nlhead] if l.strip().lower().startswith(b"startdate:")]
    if not start:
        raise ValueError("no 'Startdate:' line in header")
    ref = datetime.strptime(start[0].split(b":", 1)[1].strip().decode(), "%Y%m%d%H%M%S")
    keep, rows = lines[:nlhead], 0
    for line in lines[nlhead:]:
        parts = line.split()
        if not parts:
            continue
        ts = ref + timedelta(days=float(parts[0]))
        if t0 <= ts < t1:
            keep.append(line); rows += 1
    note = f"{rows}/{len(lines) - nlhead} rows kept (header: {nlhead} lines, ref {ref.date()})"
    return (keep if rows else None), note

station = desc["station_abbr"]
REQUIRED = {  # what the pipeline steps look up; each must match exactly one file
    "timeseries": lambda n: n.startswith(f"ACSM_{station}_") and n.endswith("_timeseries.txt"),
    "meta":       lambda n: n.startswith(f"ACSM_{station}_") and n.endswith("_meta.txt"),
    "cpc":        lambda n: "cpc.particle_number_concentration.aerosol." in n      # same keywords
                            and f"CH02L_TSI_3772_{station}.CH02L_CPC.lev1.nas" in n,   # as generate_flags
}

def write(f, lines, note):
    out = dest / f.relative_to(src)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_bytes(b"".join(lines))
    print(f"  {note:<6} {f.relative_to(src)}")

errors, written = [], []
for inst in inst_folders:
    root = src / inst
    if not root.is_dir():
        sys.exit(f"Not found: {root}  (instrument_datafolder '{inst}' under {src})")
    files = sorted(p for p in root.rglob("*") if p.is_file())

    for f in files:
        rel = f.relative_to(src)
        if "params" in rel.parts:
            write(f, [f.read_bytes()], "copy"); written.append(f.name); continue
        lines = f.read_bytes().splitlines(keepends=True)

        if f.name.startswith("Org_") and f.suffix.lower() == ".csv":
            print(f"  leave  {rel}  (not read by any pipeline step; see fixtures/README.md)")
            continue
        elif f.suffix.lower() == ".nas":
            try:
                kept, note = slice_nasa_ames(lines)
            except Exception as e:
                kept, note = None, f"not a NASA Ames layout I can read ({e})"
            if kept is None: errors.append(f"{rel}: {note}"); continue
            write(f, kept, "slice"); print(f"         {note}")
        elif f.suffix.lower() == ".txt":
            kept, note = slice_text(lines)
            if kept is None: errors.append(f"{rel}: {note}"); continue
            write(f, kept, "slice"); print(f"         {note}")
        else:
            errors.append(f"{rel}: no rule for this file type; tell me how to handle it")
            continue
        written.append(f.name)

for what, match in REQUIRED.items():
    n = sum(match(name) for name in written)
    if n != 1:
        errors.append(f"pipeline needs exactly one {what} file, fixture has {n}")

if errors:
    print("\nNOT DONE. Fix these and re-run with --force:")
    for e in errors: print("  -", e)
    sys.exit(1)

# Descriptor for fixture mode (input/output paths are overwritten by the test).
desc["test_month_range"] = f"{t0.month}-{(t1 - timedelta(seconds=1)).month}"
(repo / "tests/pipeline/fixtures/campaignDescriptor.yaml").write_text(
    yaml.safe_dump(desc, sort_keys=False, allow_unicode=True))
print(f"\nfixtures/campaignDescriptor.yaml written (test_month_range: {desc['test_month_range']})")
PY

echo
du -sh "$DEST"
echo "Next: unset ACSM_TEST_DESCRIPTOR ACSM_BASELINE_DIR; pytest tests/pipeline -s --update-baseline"
