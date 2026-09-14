#!/usr/bin/env bash
set -euo pipefail

BRANCH="research/eb-v1-operational-burden-rc1-20260913"
ROOT="$(git rev-parse --show-toplevel)"
BASE="$ROOT/research/eb_v1_operational_burden_rc1"
MANIFEST="$BASE/APPARATUS_MANIFEST_V2.json"
ORIGINAL_RUNNER="$BASE/run_rc1_with_codex.sh"

cd "$ROOT"

git fetch origin "$BRANCH" >/dev/null 2>&1 || { echo "ERROR: could not fetch origin/$BRANCH" >&2; exit 2; }
START_HEAD="$(git rev-parse HEAD)"
REMOTE_HEAD="$(git rev-parse "origin/$BRANCH")"
if [[ "$START_HEAD" != "$REMOTE_HEAD" ]]; then
  echo "ERROR: execution checkout must start exactly at current origin/$BRANCH" >&2
  echo "local=$START_HEAD remote=$REMOTE_HEAD" >&2
  exit 2
fi
if [[ -n "$(git status --porcelain)" ]]; then
  echo "ERROR: working tree must be clean before RC1 execution." >&2
  git status --short >&2
  exit 3
fi

python3 - "$ROOT" "$BASE" "$MANIFEST" <<'PY'
import hashlib
import json
import subprocess
import sys
from pathlib import Path

root = Path(sys.argv[1])
base = Path(sys.argv[2])
manifest_path = Path(sys.argv[3])
manifest = json.loads(manifest_path.read_text(encoding="utf-8"))

if manifest.get("schema") != "eb-v1-operational-burden-rc1-apparatus-manifest-v2":
    raise SystemExit("apparatus manifest V2 schema mismatch")

for rel, expected in manifest["git_blob_sha1"].items():
    path = base / rel
    if not path.is_file():
        raise SystemExit(f"missing apparatus file: {rel}")
    got = subprocess.check_output(
        ["git", "-C", str(root), "hash-object", "--", str(path)],
        text=True,
    ).strip()
    if got != expected:
        raise SystemExit(f"apparatus git-blob mismatch: {rel}: {got} != {expected}")

for rel, expected in manifest["packet_canonical_sha256"].items():
    path = base / rel
    obj = json.loads(path.read_text(encoding="utf-8"))
    canonical = json.dumps(
        obj,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
    ).encode("utf-8")
    got = hashlib.sha256(canonical).hexdigest()
    if got != expected:
        raise SystemExit(f"packet canonical hash mismatch: {rel}: {got} != {expected}")

print("APPARATUS_V2_IDENTITY_VALID")
PY

# Preserve the original failed V1 runner as evidence. Execute a temporary copy
# with only its defective raw-SHA preflight block removed. All downstream RC1
# mechanics remain byte-for-byte from the frozen original runner.
TMP_RUNNER="$(mktemp "${TMPDIR:-/tmp}/eb-v1-rc1-runner-v2.XXXXXX.sh")"
trap 'rm -f "$TMP_RUNNER"' EXIT

python3 - "$ORIGINAL_RUNNER" "$TMP_RUNNER" <<'PY'
import sys
from pathlib import Path

src = Path(sys.argv[1]).read_text(encoding="utf-8").splitlines()
out = []
start = 'python3 - "$BASE" "$MANIFEST" <<\'PY\''
skipping = False
found = False
finished = False

for line in src:
    if not skipping and not found and line == start:
        skipping = True
        found = True
        continue
    if skipping:
        if line == "PY":
            skipping = False
            finished = True
        continue
    out.append(line)

if not found or not finished or skipping:
    raise SystemExit("could not isolate defective V1 apparatus preflight block")

Path(sys.argv[2]).write_text("\n".join(out) + "\n", encoding="utf-8")
PY

chmod 700 "$TMP_RUNNER"
exec bash "$TMP_RUNNER"
