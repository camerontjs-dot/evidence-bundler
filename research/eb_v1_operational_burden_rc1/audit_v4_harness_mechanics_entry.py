#!/usr/bin/env python3
from pathlib import Path
import sys

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

import audit_v4_harness_mechanics as audit

# The preserved first audit helper calculated the repo root one parent too high.
# Correct that mechanical-only defect without rewriting the preserved helper.
audit.REPO = HERE.parents[1]
audit.main()
