from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

EXPECTED = {
    "C06_HARD_NEG:child:1": "C06-P1",
    "RETRIEVAL_APERTURE:child:1": "RET-AP-P6",
}


def sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--selection", required=True)
    parser.add_argument("--output", required=True)
    args = parser.parse_args()

    source = Path(args.selection)
    payload = json.loads(source.read_text(encoding="utf-8"))
    results = {}
    for lane in payload["lanes"]:
        proposition_id = str(lane["proposition_id"])
        expected = EXPECTED[proposition_id]
        results[proposition_id] = {
            "expected_known_keep": expected,
            "arms": {
                name: {"selected": selected, "rescued": expected in selected}
                for name, selected in lane["arms"].items()
            },
        }

    output = {
        "schema": "eb-typed-selector-rc0-known-case-evaluation-v1",
        "classification": "RETROSPECTIVE_DEVELOPMENT_DIAGNOSTIC_ONLY",
        "selection_sha256": sha256_file(source),
        "known_case_authority": {
            "C06_HARD_NEG:child:1|C06-P1": "PR #77 operational KEEP_DISTINCT deep miss",
            "RETRIEVAL_APERTURE:child:1|RET-AP-P6": "PR #77 operational KEEP_DISTINCT deep miss",
        },
        "results": results,
        "nonclaims": [
            "This evaluation is answer-bearing and runs only after selector output is frozen.",
            "Passing these known cases is development evidence only and is not a research disposition.",
        ],
    }
    text = json.dumps(output, sort_keys=True, separators=(",", ":")) + "\n"
    Path(args.output).write_text(text, encoding="utf-8")
    print(hashlib.sha256(text.encode("utf-8")).hexdigest())
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
