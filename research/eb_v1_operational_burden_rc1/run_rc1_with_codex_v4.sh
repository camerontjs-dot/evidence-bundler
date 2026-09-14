#!/usr/bin/env bash
set -euo pipefail

BRANCH="research/eb-v1-operational-burden-rc1-20260913"
ROOT="$(git rev-parse --show-toplevel)"
cd "$ROOT"
BASE="$ROOT/research/eb_v1_operational_burden_rc1"
MANIFEST="$BASE/APPARATUS_MANIFEST_V3.json"
ORIGINAL_RUNNER="$BASE/run_rc1_with_codex.sh"

command -v codex >/dev/null 2>&1 || { echo "ERROR: codex CLI not found on PATH." >&2; exit 4; }
command -v tr >/dev/null 2>&1 || { echo "ERROR: tr not found on PATH." >&2; exit 4; }
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

TMP_DIR="$(mktemp -d "${TMPDIR:-/tmp}/eb-v1-rc1-v4.XXXXXX")"
trap 'rm -rf "$TMP_DIR"' EXIT
CORRECTED_COBALT_RUBRIC="$TMP_DIR/OPERATIONAL_REVIEW_RUBRIC_COBALT_V4.md"
TMP_RUNNER="$TMP_DIR/run_rc1_with_codex_v4_inner.sh"

# Same V3 identity, structure and supervisor-map preflight.
python3 - "$ROOT" "$BASE" "$MANIFEST" "$CORRECTED_COBALT_RUBRIC" <<'PY'
import hashlib
import json
import subprocess
import sys
from pathlib import Path

root = Path(sys.argv[1])
base = Path(sys.argv[2])
manifest_path = Path(sys.argv[3])
corrected_rubric = Path(sys.argv[4])
manifest = json.loads(manifest_path.read_text(encoding='utf-8'))

if manifest.get('schema') != 'eb-v1-operational-burden-rc1-apparatus-manifest-v3':
    raise SystemExit('apparatus manifest V3 schema mismatch')

for rel, expected in manifest['git_blob_sha1'].items():
    path = base / rel
    if not path.is_file():
        raise SystemExit(f'missing apparatus file: {rel}')
    got = subprocess.check_output(
        ['git', '-C', str(root), 'hash-object', '--', str(path)],
        text=True,
    ).strip()
    if got != expected:
        raise SystemExit(f'apparatus git-blob mismatch: {rel}: {got} != {expected}')


def canonical_hash(path: Path) -> str:
    obj = json.loads(path.read_text(encoding='utf-8'))
    raw = json.dumps(obj, sort_keys=True, separators=(',', ':'), ensure_ascii=False).encode('utf-8')
    return hashlib.sha256(raw).hexdigest()

for rel, expected in manifest['packet_canonical_sha256'].items():
    got = canonical_hash(base / rel)
    if got != expected:
        raise SystemExit(f'packet canonical hash mismatch: {rel}: {got} != {expected}')

amber = json.loads((base / 'BLIND_REVIEW_PACKET_AMBER.json').read_text(encoding='utf-8'))
cobalt = json.loads((base / 'BLIND_REVIEW_PACKET_COBALT.json').read_text(encoding='utf-8'))
sup = json.loads((base / 'SUPERVISOR_RELATION_MAP.json').read_text(encoding='utf-8'))
exp = manifest['structural_expectations']

if amber.get('set_id') != exp['amber_set_id'] or cobalt.get('set_id') != exp['cobalt_set_id']:
    raise SystemExit('packet set_id mismatch')
if len(amber.get('lanes', [])) != exp['amber_lane_count']:
    raise SystemExit('amber lane-count mismatch')
if len(cobalt.get('lanes', [])) != exp['cobalt_lane_count']:
    raise SystemExit('cobalt lane-count mismatch')


def packet_ids(packet):
    ids=[]
    for lane in packet.get('lanes', []):
        for passage in lane.get('passages', []):
            rid=passage.get('relation_id')
            if not isinstance(rid, str):
                raise SystemExit('packet relation_id missing')
            ids.append(rid)
    if len(ids) != len(set(ids)):
        raise SystemExit('duplicate relation_id in packet')
    return ids

a_ids = packet_ids(amber)
c_ids = packet_ids(cobalt)
if len(a_ids) != exp['amber_relationship_count']:
    raise SystemExit('amber relationship-count mismatch')
if len(c_ids) != exp['cobalt_relationship_count']:
    raise SystemExit('cobalt relationship-count mismatch')

matched = sup.get('matched_relationships', [])
large_only = sup.get('larger_arm_only_relationships', [])
if len(matched) != exp['matched_relationship_count']:
    raise SystemExit('supervisor matched relationship-count mismatch')
if len(large_only) != exp['larger_arm_only_relationship_count']:
    raise SystemExit('supervisor larger-only relationship-count mismatch')
if len({row.get('proposition_id') for row in matched}) != exp['normative_lane_count']:
    raise SystemExit('supervisor normative-lane-count mismatch')

expected_a = {row['amber_relation_id'] for row in matched}
expected_c = {row['cobalt_relation_id'] for row in matched} | {row['relation_id'] for row in large_only}
if set(a_ids) != expected_a:
    raise SystemExit('amber packet relation set does not match supervisor map')
if set(c_ids) != expected_c:
    raise SystemExit('cobalt packet relation set does not match supervisor map')

patch = manifest['cobalt_rubric_hash_patch']
source = (base / patch['source_file']).read_text(encoding='utf-8')
stale = patch['stale_literal']
correct = patch['correct_literal']
if source.count(stale) != patch['required_stale_occurrences_before']:
    raise SystemExit('unexpected stale cobalt hash occurrence count in source rubric')
patched = source.replace(stale, correct)
if patched.count(stale) != patch['required_stale_occurrences_after']:
    raise SystemExit('stale cobalt hash remained after deterministic rubric patch')
if patched.count(correct) != patch['required_correct_occurrences_after']:
    raise SystemExit('correct cobalt hash occurrence count mismatch after rubric patch')
corrected_rubric.write_text(patched, encoding='utf-8')

print('APPARATUS_V4_IDENTITY_VALID')
print('PACKET_SUPERVISOR_RELATION_SETS_VALID')
print('COBALT_RUBRIC_IDENTITY_PATCH_VALID')
PY

# Generate the same frozen inner runner as V3, plus a portability-only rewrite
# of the two Bash-4 uppercase expansions used in child output filenames.
python3 - "$ORIGINAL_RUNNER" "$TMP_RUNNER" "$CORRECTED_COBALT_RUBRIC" <<'PY'
import sys
from pathlib import Path

src = Path(sys.argv[1]).read_text(encoding='utf-8').splitlines()
out = []
start = 'python3 - "$BASE" "$MANIFEST" <<\'PY\''
skipping = False
found_preflight = False
finished_preflight = False
replaced_rubric = 0
portable_replacements = 0
inserted_upper_vars = False

for line in src:
    if not skipping and not found_preflight and line == start:
        skipping = True
        found_preflight = True
        continue
    if skipping:
        if line == 'PY':
            skipping = False
            finished_preflight = True
        continue

    if line == '  local work final trace':
        out.append('  local work final trace phase_upper set_upper')
        continue

    if line == '  final="$out_dir/${phase^^}_${set_name^^}_${ordinal}.json"':
        if not inserted_upper_vars:
            out.append('  phase_upper="$(printf \'%s\' "$phase" | tr \'[:lower:]\' \'[:upper:]\')"')
            out.append('  set_upper="$(printf \'%s\' "$set_name" | tr \'[:lower:]\' \'[:upper:]\')"')
            inserted_upper_vars = True
        out.append('  final="$out_dir/${phase_upper}_${set_upper}_${ordinal}.json"')
        portable_replacements += 1
        continue

    if line == '  trace="$out_dir/${phase^^}_${set_name^^}_${ordinal}.trace.jsonl"':
        out.append('  trace="$out_dir/${phase_upper}_${set_upper}_${ordinal}.trace.jsonl"')
        portable_replacements += 1
        continue

    if line == 'C_RUBRIC="$BASE/OPERATIONAL_REVIEW_RUBRIC_COBALT.md"':
        out.append(f'C_RUBRIC={sys.argv[3]!r}')
        replaced_rubric += 1
    else:
        out.append(line)

if not found_preflight or not finished_preflight or skipping:
    raise SystemExit('could not isolate defective V1 apparatus preflight block')
if replaced_rubric != 1:
    raise SystemExit(f'expected one cobalt rubric source replacement, got {replaced_rubric}')
if portable_replacements != 2 or not inserted_upper_vars:
    raise SystemExit(f'expected exactly two Bash portability replacements, got {portable_replacements}')

text = '\n'.join(out) + '\n'
if '${phase^^}' in text or '${set_name^^}' in text:
    raise SystemExit('Bash-4 uppercase expansion remains after V4 portability rewrite')
Path(sys.argv[2]).write_text(text, encoding='utf-8')
PY

chmod 700 "$TMP_RUNNER"

# Parse with the exact Bash executable that will run the experiment before any child launch.
bash -n "$TMP_RUNNER"
echo "BASH_PORTABILITY_REWRITE_VALID"

bash "$TMP_RUNNER"
