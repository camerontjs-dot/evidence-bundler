#!/usr/bin/env bash
set -euo pipefail

BRANCH="research/eb-v1-operational-burden-rc1-20260913"
ROOT="$(git rev-parse --show-toplevel)"
cd "$ROOT"
BASE="$ROOT/research/eb_v1_operational_burden_rc1"
REF_OUT="$BASE/reference_outputs"
TEST_OUT="$BASE/test_outputs"
MANIFEST="$BASE/APPARATUS_MANIFEST.json"

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
command -v codex >/dev/null 2>&1 || { echo "ERROR: codex CLI not found on PATH." >&2; exit 4; }

python3 - "$BASE" "$MANIFEST" <<'PY'
import hashlib,json,sys
from pathlib import Path
base=Path(sys.argv[1]); manifest=json.loads(Path(sys.argv[2]).read_text())
if manifest.get('schema')!='eb-v1-operational-burden-rc1-apparatus-manifest-v1': raise SystemExit('apparatus manifest schema mismatch')
for rel,expected in manifest['sha256'].items():
    p=base/rel
    if not p.is_file(): raise SystemExit(f'missing apparatus file: {rel}')
    got=hashlib.sha256(p.read_bytes()).hexdigest()
    if got!=expected: raise SystemExit(f'apparatus hash mismatch: {rel}: {got} != {expected}')
print('APPARATUS_HASHES_VALID')
PY

mkdir -p "$REF_OUT" "$TEST_OUT"
printf '%s\n' "$(codex --version 2>&1 | head -n 1)" > "$REF_OUT/CODEX_VERSION.txt"
PROMPT_BASE='CONTEXT-FREE REQUIRED. You are a fresh isolated semantic reviewer. Use only BLIND_REVIEW_PACKET.json and OPERATIONAL_REVIEW_RUBRIC.md in the current working directory. Your only authorized shell command is exactly: cat BLIND_REVIEW_PACKET.json OPERATIONAL_REVIEW_RUBRIC.md. Do not inspect parent directories, GitHub, the internet, other files, another set, another reviewer output, prior references, prior experiment results, or expected outcomes. Read both authorized files completely and apply the rubric exactly. Return only the required JSON object, with no markdown fences and no commentary.'

validate_trace() {
  local trace="$1"
  python3 - "$trace" <<'PY'
import json,sys
from pathlib import Path
allowed={"/bin/zsh -lc 'cat BLIND_REVIEW_PACKET.json OPERATIONAL_REVIEW_RUBRIC.md'","/bin/bash -lc 'cat BLIND_REVIEW_PACKET.json OPERATIONAL_REVIEW_RUBRIC.md'","cat BLIND_REVIEW_PACKET.json OPERATIONAL_REVIEW_RUBRIC.md"}
for line in Path(sys.argv[1]).read_text(encoding='utf-8').splitlines():
    if not line.strip(): continue
    obj=json.loads(line); item=obj.get('item') or {}
    if item.get('type')=='command_execution' and item.get('command') not in allowed:
        raise SystemExit(f"forbidden/unexpected child command: {item.get('command')}")
print('TRACE_APERTURE_VALID')
PY
}

validate_one() {
  local packet="$1" review="$2" phase="$3" ids_file="$4"
  PYTHONPATH="$BASE" python3 - "$packet" "$review" "$phase" "$ids_file" <<'PY'
import json,sys
from pathlib import Path
from review_common import validate_review
packet=Path(sys.argv[1]); review=Path(sys.argv[2]); phase=sys.argv[3]; ids_file=Path(sys.argv[4])
used=set(json.loads(ids_file.read_text())) if ids_file.exists() else set()
_,reviewer_id=validate_review(review,packet,phase,used)
ids_file.write_text(json.dumps(sorted(used))+'\n')
print('VALID',reviewer_id)
PY
}

run_child() {
  local set_name="$1" phase="$2" ordinal="$3" packet_source="$4" rubric_source="$5" out_dir="$6" ids_file="$7"
  local work final trace
  work="$(mktemp -d "${TMPDIR:-/tmp}/eb-v1-rc1-review.XXXXXX")"
  cp "$packet_source" "$work/BLIND_REVIEW_PACKET.json"
  cp "$rubric_source" "$work/OPERATIONAL_REVIEW_RUBRIC.md"
  final="$out_dir/${phase^^}_${set_name^^}_${ordinal}.json"
  trace="$out_dir/${phase^^}_${set_name^^}_${ordinal}.trace.jsonl"
  local prompt="$PROMPT_BASE Set reviewer.review_phase exactly to \"$phase\"."
  echo "Launching isolated $phase reviewer $set_name-$ordinal"
  if ! (cd "$work" && codex exec --ephemeral --ignore-user-config --ignore-rules --skip-git-repo-check --sandbox read-only --json --output-last-message "$final" "$prompt" > "$trace"); then
    echo "ERROR: child execution failed: $phase $set_name $ordinal" >&2
    echo "Preserved workspace: $work" >&2
    exit 10
  fi
  validate_trace "$trace"
  validate_one "$work/BLIND_REVIEW_PACKET.json" "$final" "$phase" "$ids_file"
  rm -rf "$work"
}

A_PACKET="$BASE/BLIND_REVIEW_PACKET_AMBER.json"
C_PACKET="$BASE/BLIND_REVIEW_PACKET_COBALT.json"
A_RUBRIC="$BASE/OPERATIONAL_REVIEW_RUBRIC_AMBER.md"
C_RUBRIC="$BASE/OPERATIONAL_REVIEW_RUBRIC_COBALT.md"
IDS_FILE="$BASE/.rc1_reviewer_ids.json"
rm -f "$IDS_FILE"

for i in 1 2 3; do run_child amber reference "$i" "$A_PACKET" "$A_RUBRIC" "$REF_OUT" "$IDS_FILE"; done
for i in 1 2 3; do run_child cobalt reference "$i" "$C_PACKET" "$C_RUBRIC" "$REF_OUT" "$IDS_FILE"; done

PYTHONPATH="$BASE" python3 "$BASE/consolidate_references.py" \
  --amber-packet "$A_PACKET" --cobalt-packet "$C_PACKET" \
  --amber-r1 "$REF_OUT/REFERENCE_AMBER_1.json" --amber-r2 "$REF_OUT/REFERENCE_AMBER_2.json" --amber-r3 "$REF_OUT/REFERENCE_AMBER_3.json" \
  --cobalt-r1 "$REF_OUT/REFERENCE_COBALT_1.json" --cobalt-r2 "$REF_OUT/REFERENCE_COBALT_2.json" --cobalt-r3 "$REF_OUT/REFERENCE_COBALT_3.json" \
  --out-dir "$REF_OUT"

python3 - "$REF_OUT" <<'PY'
import hashlib,json,sys
from pathlib import Path
out=Path(sys.argv[1]); receipt={'schema':'eb-v1-operational-burden-rc1-stage1-file-receipt-v1','files':{}}
for p in sorted(out.iterdir()):
    if p.is_file(): receipt['files'][p.name]={'sha256':hashlib.sha256(p.read_bytes()).hexdigest()}
(out/'STAGE1_FILE_RECEIPT.json').write_text(json.dumps(receipt,indent=2,sort_keys=True)+'\n')
PY

rm -f "$IDS_FILE"
git add "$REF_OUT"
git commit -m "research: freeze RC1 task-aligned reference"
REFERENCE_FREEZE_COMMIT="$(git rev-parse HEAD)"
git push origin "HEAD:$BRANCH"
echo "Stage 1 frozen and pushed: $REFERENCE_FREEZE_COMMIT"

python3 - "$REF_OUT/REFERENCE_FREEZE_RECEIPT.json" "$IDS_FILE" <<'PY'
import json,sys
r=json.load(open(sys.argv[1])); ids=[]
for info in r['sets'].values(): ids.extend(info['reviewer_ids'])
open(sys.argv[2],'w').write(json.dumps(sorted(ids))+'\n')
PY
printf '%s\n' "$(codex --version 2>&1 | head -n 1)" > "$TEST_OUT/CODEX_VERSION.txt"
for i in 1 2; do run_child amber test "$i" "$A_PACKET" "$A_RUBRIC" "$TEST_OUT" "$IDS_FILE"; done
for i in 1 2; do run_child cobalt test "$i" "$C_PACKET" "$C_RUBRIC" "$TEST_OUT" "$IDS_FILE"; done

PYTHONPATH="$BASE" python3 "$BASE/evaluate_rc1.py" \
  --map "$BASE/SUPERVISOR_RELATION_MAP.json" \
  --amber-packet "$A_PACKET" --cobalt-packet "$C_PACKET" \
  --amber-reference "$REF_OUT/REFERENCE_AMBER.json" --cobalt-reference "$REF_OUT/REFERENCE_COBALT.json" \
  --amber-t1 "$TEST_OUT/TEST_AMBER_1.json" --amber-t2 "$TEST_OUT/TEST_AMBER_2.json" \
  --cobalt-t1 "$TEST_OUT/TEST_COBALT_1.json" --cobalt-t2 "$TEST_OUT/TEST_COBALT_2.json" \
  --reference-freeze-commit "$REFERENCE_FREEZE_COMMIT" --out "$BASE/TERMINAL_RESULT.json"

python3 - "$BASE" <<'PY'
import hashlib,json,sys
from pathlib import Path
base=Path(sys.argv[1]); result=json.loads((base/'TERMINAL_RESULT.json').read_text())
receipt={'schema':'eb-v1-operational-burden-rc1-stage2-file-receipt-v1','files':{}}
for p in sorted((base/'test_outputs').iterdir()):
    if p.is_file(): receipt['files'][p.name]={'sha256':hashlib.sha256(p.read_bytes()).hexdigest()}
(base/'test_outputs'/'STAGE2_FILE_RECEIPT.json').write_text(json.dumps(receipt,indent=2,sort_keys=True)+'\n')
summary=f'''# Evidence Bundler V1 — Task-Aligned Operational Burden RC1 Results\n\nPrimary disposition: **{result["primary_disposition"]}**\n\nPrimary conclusion: `{result["primary_conclusion"]}`\n\n- scoreable matched relationships: `{result["scoreable_matched_relationship_count"]} / {result["shared_relationship_count"]}`\n- scoreable normative lanes: `{result["scoreable_lane_count"]} / 18`\n- coverage guard: `{result["coverage_guard_pass"]}`\n- larger arm: `{result["larger_arm"]}`\n- smaller arm: `{result["smaller_arm"]}`\n- larger-worse flags: `{json.dumps(result["larger_worse_flags"], sort_keys=True)}`\n\nThis is a bounded model-review operational-stability result only. No merge, release, tag, production-default change, or V1 promotion is authorized by this record.\n\nStop boundary applies.\n'''
(base/'RESULTS.md').write_text(summary)
PY

rm -f "$IDS_FILE"
git add "$TEST_OUT" "$BASE/TERMINAL_RESULT.json" "$BASE/RESULTS.md"
git commit -m "research: freeze RC1 operational burden result"
git push origin "HEAD:$BRANCH"

echo
echo "RC1 COMPLETE"
echo "REFERENCE_FREEZE_COMMIT=$REFERENCE_FREEZE_COMMIT"
echo "FINAL_COMMIT=$(git rev-parse HEAD)"
python3 - "$BASE/TERMINAL_RESULT.json" <<'PY'
import json,sys
r=json.load(open(sys.argv[1])); print('PRIMARY_DISPOSITION='+r['primary_disposition']); print('PRIMARY_CONCLUSION='+r['primary_conclusion'])
PY
