#!/usr/bin/env python3
from pathlib import Path
import json
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

# V4 must retain the parse gate and the explicit removal check for the two
# Bash-4-only uppercase expansions before any child process could launch.
v4 = (HERE / 'run_rc1_with_codex_v4.sh').read_text(encoding='utf-8')
required = [
    'bash -n "$TMP_RUNNER"',
    "if '${phase^^}' in text or '${set_name^^}' in text",
    "tr '[:lower:]' '[:upper:]'",
]
missing = [needle for needle in required if needle not in v4]
if missing:
    raise SystemExit(f'V4 portability gate missing: {missing}')

audit.main()
