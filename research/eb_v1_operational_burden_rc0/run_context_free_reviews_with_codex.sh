#!/usr/bin/env bash
set -euo pipefail

# Evidence Bundler V1 Operational Review Burden RC0
# Launch four fresh, isolated Codex semantic-review executions.
# Scientific rule: each child sees exactly one blind packet plus its matching rubric.

ROOT="$(git rev-parse --show-toplevel)"
BASE="$ROOT/research/eb_v1_operational_burden_rc0"
OUT="$BASE/codex_review_outputs"
mkdir -p "$OUT"

if ! command -v codex >/dev/null 2>&1; then
  echo "ERROR: codex CLI is not available on PATH." >&2
  exit 2
fi

CODEX_VERSION="$(codex --version 2>&1 | head -n 1 || true)"
printf '%s\n' "$CODEX_VERSION" > "$OUT/CODEX_VERSION.txt"

PROMPT='CONTEXT-FREE REQUIRED. Use only BLIND_REVIEW_PACKET.json and REVIEWER_RUBRIC.md in the current working directory. Do not inspect parent directories, GitHub, the internet, other files, other review sets, prior results, or another reviewer output. Read both authorized files completely. Perform the semantic materiality review exactly as specified by REVIEWER_RUBRIC.md. Return only the required JSON object, with no markdown fences and no commentary.'

validate_review() {
  local packet="$1"
  local review="$2"
  local expected_count="$3"
  local expected_hash="$4"

  python3 - "$packet" "$review" "$expected_count" "$expected_hash" <<'PY'
import json, sys
from pathlib import Path

packet_path = Path(sys.argv[1])
review_path = Path(sys.argv[2])
expected_count = int(sys.argv[3])
expected_hash = sys.argv[4]

packet = json.loads(packet_path.read_text(encoding="utf-8"))
review = json.loads(review_path.read_text(encoding="utf-8"))

if review.get("schema") != "eb-v1-operational-review-result-v1":
    raise SystemExit("review schema mismatch")
meta = review.get("reviewer", {})
if meta.get("packet_canonical_sha256") != expected_hash:
    raise SystemExit("packet canonical hash mismatch")
if meta.get("independent_of_other_reviewers") is not True:
    raise SystemExit("independence assertion missing")
if meta.get("saw_other_review_set") is not False:
    raise SystemExit("reviewer reports seeing another review set")

items = packet.get("relationships")
if items is None:
    items = packet.get("items")
if not isinstance(items, list):
    raise SystemExit("packet relationship array not found")

packet_ids = []
for item in items:
    rid = item.get("relation_id")
    if not isinstance(rid, str):
        raise SystemExit("packet relation_id missing")
    packet_ids.append(rid)

judgments = review.get("judgments")
if not isinstance(judgments, list) or len(judgments) != expected_count:
    raise SystemExit(f"expected {expected_count} judgments")

allowed = {"MATERIAL_FOR_PROPOSITION", "NONMATERIAL_FOR_PROPOSITION", "UNRESOLVED"}
seen = []
for judgment in judgments:
    rid = judgment.get("relation_id")
    label = judgment.get("label")
    if not isinstance(rid, str) or label not in allowed:
        raise SystemExit("invalid judgment")
    seen.append(rid)

if len(set(seen)) != len(seen):
    raise SystemExit("duplicate relation_id in review")
if set(seen) != set(packet_ids):
    raise SystemExit("review relation_id set does not match packet")
if len(packet_ids) != expected_count:
    raise SystemExit("packet count differs from frozen expectation")

print("VALID")
PY
}

run_one() {
  local neutral_arm="$1"
  local ordinal="$2"
  local packet_source="$3"
  local rubric_source="$4"
  local expected_count="$5"
  local expected_hash="$6"

  local work
  work="$(mktemp -d "${TMPDIR:-/tmp}/eb-v1-codex-review.XXXXXX")"

  cp "$packet_source" "$work/BLIND_REVIEW_PACKET.json"
  cp "$rubric_source" "$work/REVIEWER_RUBRIC.md"

  local final_out="$OUT/REVIEW_${neutral_arm}_${ordinal}.json"
  local trace_out="$OUT/REVIEW_${neutral_arm}_${ordinal}.trace.jsonl"

  echo "Launching isolated reviewer ${neutral_arm}-${ordinal}"

  if ! (
    cd "$work"
    codex exec \
      --ephemeral \
      --ignore-user-config \
      --ignore-rules \
      --skip-git-repo-check \
      --sandbox read-only \
      --json \
      --output-last-message "$final_out" \
      "$PROMPT" \
      > "$trace_out"
  ); then
    echo "ERROR: Codex reviewer ${neutral_arm}-${ordinal} failed. Preserving isolated workspace for diagnosis: $work" >&2
    exit 3
  fi

  if ! validate_review "$work/BLIND_REVIEW_PACKET.json" "$final_out" "$expected_count" "$expected_hash"; then
    echo "ERROR: reviewer ${neutral_arm}-${ordinal} failed structural validation. Preserving isolated workspace: $work" >&2
    exit 4
  fi

  rm -rf "$work"
}

# The supervisor may know the neutral arm names. Child executions do not receive
# the arm-to-profile mapping, predecessor results, gold, or any repository context.
run_one "AMBER" 1 \
  "$BASE/BLIND_REVIEW_PACKET_AMBER.json" \
  "$BASE/REVIEWER_RUBRIC_AMBER.md" \
  54 \
  "c0255cb02a20f43179bbf6e2ba1117a38dbbd158ecac6c34e22eac926286c731"

run_one "AMBER" 2 \
  "$BASE/BLIND_REVIEW_PACKET_AMBER.json" \
  "$BASE/REVIEWER_RUBRIC_AMBER.md" \
  54 \
  "c0255cb02a20f43179bbf6e2ba1117a38dbbd158ecac6c34e22eac926286c731"

run_one "COBALT" 1 \
  "$BASE/BLIND_REVIEW_PACKET_COBALT.json" \
  "$BASE/REVIEWER_RUBRIC_COBALT.md" \
  96 \
  "9692386b125c73520fbdbd3c3f61b0c0b020f35b57b089cbd1bb17f662043675"

run_one "COBALT" 2 \
  "$BASE/BLIND_REVIEW_PACKET_COBALT.json" \
  "$BASE/REVIEWER_RUBRIC_COBALT.md" \
  96 \
  "9692386b125c73520fbdbd3c3f61b0c0b020f35b57b089cbd1bb17f662043675"

python3 - "$OUT" <<'PY'
import hashlib, json, sys
from pathlib import Path

out = Path(sys.argv[1])
receipt = {
    "schema": "eb-v1-operational-review-codex-launch-receipt-v1",
    "review_files": {},
}
for path in sorted(out.glob("REVIEW_*.json")):
    receipt["review_files"][path.name] = {
        "sha256": hashlib.sha256(path.read_bytes()).hexdigest()
    }
(out / "CODEX_LAUNCH_RECEIPT.json").write_text(
    json.dumps(receipt, indent=2, sort_keys=True) + "\n",
    encoding="utf-8",
)
print(json.dumps(receipt, indent=2, sort_keys=True))
PY

echo
echo "SUCCESS: four isolated Codex reviews are in:"
echo "$OUT"
echo "Do not inspect or edit the review JSON files before freezing/evaluation."
