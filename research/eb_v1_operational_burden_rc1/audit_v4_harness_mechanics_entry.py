#!/usr/bin/env python3
from pathlib import Path
import json
import subprocess
import sys

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

import audit_v4_harness_mechanics as audit

# The preserved first audit helper calculated the repo root one parent too high.
# Correct that mechanical-only defect without rewriting the preserved helper.
audit.REPO = HERE.parents[1]

# Fail closed on the frozen arm mapping before any structural comparison.
sup = json.loads((HERE / 'SUPERVISOR_RELATION_MAP.json').read_text(encoding='utf-8'))
if sup.get('arm_mapping') != {'amber': '5/3', 'cobalt': '10/7'}:
    raise SystemExit(f"arm mapping mismatch: {sup.get('arm_mapping')}")

# The audit may inspect only the preserved V4 execution worktree. Do not allow
# a reconstructed or later checkout to masquerade as the failed V4 source.
try:
    i = sys.argv.index('--failed-worktree')
    failed_worktree = Path(sys.argv[i + 1]).resolve()
except (ValueError, IndexError):
    raise SystemExit('--failed-worktree is required')

expected_v4_head = 'ebed6c29b31614687c0b3d7b0f05444482166abd'
try:
    failed_head = subprocess.check_output(
        ['git', '-C', str(failed_worktree), 'rev-parse', 'HEAD'], text=True
    ).strip()
except Exception as exc:
    raise SystemExit(f'cannot read preserved V4 worktree HEAD: {exc}')
if failed_head != expected_v4_head:
    raise SystemExit(f'preserved V4 worktree HEAD mismatch: {failed_head} != {expected_v4_head}')

# V4 portability checks are source-generation invariants, not a literal search
# for the generated shell text. The tr commands are embedded inside Python
# string literals in run_rc1_with_codex_v4.sh and therefore appear escaped in
# the source file. Check the actual fail-closed invariants instead.
v4 = (HERE / 'run_rc1_with_codex_v4.sh').read_text(encoding='utf-8')
required = [
    'bash -n "$TMP_RUNNER"',
    "if '${phase^^}' in text or '${set_name^^}' in text",
    'portable_replacements != 2',
    'phase_upper',
    'set_upper',
    "tr \\'[:lower:]\\' \\'[:upper:]\\'",
]
missing = [needle for needle in required if needle not in v4]
if missing:
    raise SystemExit(f'V4 portability gate missing: {missing}')

# The generator must still fail closed unless exactly the two expected Bash-4
# expansions were replaced before parsing/execution.
if v4.count('portable_replacements += 1') != 2:
    raise SystemExit('V4 portability replacement accounting changed')

# This audit is mechanical only. audit.main() launches no Codex reviewer.
audit.main()
